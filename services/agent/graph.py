"""Compiled support-agent graph.

Each node does one job. Retrieval and answer generation stay in data.pipelines.rag.
Ticket and inventory reads go through the MCP server. `query()` is not used here.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from data.pipelines.rag import NOT_ENOUGH, generate_answer, minimum_score, retrieve
from services.agent.guardrails import check_output, isolate, screen_message
from services.agent.mcp_client import RemoteMCPClient
from services.agent.memory import (
    APPROVED_REPLY,
    EDITED_REPLY,
    FORBIDDEN_REPLY,
    PROPOSAL_QUESTION,
    REJECTED_REPLY,
    MemoryRefusal,
    MemoryStore,
    classify_decision,
    fact_key,
    parse_structured_reply,
    proposal_for,
)
from services.agent.tools import (
    INVENTORY_UNAVAILABLE,
    TICKET_UNAVAILABLE,
    TOOL_TIMEOUT_SECONDS,
    format_products,
    format_tickets,
    plan_sources,
    run_tool,
)

EMPTY_QUESTION = "Enter a question."


class AgentState(TypedDict, total=False):
    """Only the fields the next node needs. This is not a conversation history."""

    question: str
    context: list[dict]
    answer: str
    error: str
    trace: list[dict]
    use_rag: bool
    use_ticket: bool
    use_inventory: bool
    ticket_query: dict
    product: str
    ticket_result: dict
    inventory_result: dict
    ticket_failed: bool
    inventory_failed: bool
    thread_id: str
    memory_note: str
    stop_after_decision: bool
    memory_proposal: dict
    model_proposal: dict
    structured_reply: bool
    guard_stop: bool


def _note(state: AgentState, node: str, output: str) -> list[dict]:
    trace = [dict(step) for step in state.get("trace") or []]
    trace.append({"node": node, "output": output})
    return trace


def receive_question(state: AgentState) -> dict:
    """Accept a question, or stop with a clear error when it is blank."""
    question = str(state.get("question") or "").strip()
    if not question:
        return {
            "question": "",
            "context": [],
            "answer": "",
            "error": EMPTY_QUESTION,
            "trace": _note(state, "receive_question", "empty question"),
        }
    return {
        "question": question,
        "error": "",
        "trace": _note(state, "receive_question", "question accepted"),
    }


def choose_sources(state: AgentState) -> dict:
    """Pick the manuals, a tool, or both from the question. The user does not name the source."""
    plan = plan_sources(state.get("question") or "")
    return {
        "use_rag": plan["use_rag"],
        "use_ticket": plan["use_ticket"],
        "use_inventory": plan["use_inventory"],
        "ticket_query": plan["ticket_query"],
        "product": plan["product"],
        "trace": _note(state, "choose_sources", plan["sources"]),
    }


def _spoken(state: AgentState, answer: str) -> str:
    note = str(state.get("memory_note") or "").strip()
    if note and note not in answer:
        return f"{note} {answer}".strip()
    return answer


def route_after_plan(state: AgentState) -> str:
    if state.get("use_ticket"):
        return "lookup_ticket"
    if state.get("use_inventory"):
        return "lookup_inventory"
    if state.get("use_rag"):
        return "retrieve_context"
    return END


def route_after_ticket(state: AgentState) -> str:
    if state.get("use_inventory"):
        return "lookup_inventory"
    if state.get("use_rag"):
        return "retrieve_context"
    return "report_tools"


def route_after_inventory(state: AgentState) -> str:
    if state.get("use_rag"):
        return "retrieve_context"
    return "report_tools"


def route_after_retrieve(state: AgentState) -> str:
    if state.get("context"):
        return "generate_answer"
    if state.get("use_ticket") or state.get("use_inventory"):
        return "report_tools"
    return "honest_answer"


def build_graph(
    *,
    search=None,
    complete=None,
    checkpointer=None,
    mcp_client=None,
    tool_timeout: float | None = None,
    memory: MemoryStore | None = None,
):
    """Compile the graph. A missing node or edge fails here, before any run."""
    timeout = TOOL_TIMEOUT_SECONDS if tool_timeout is None else tool_timeout
    client = mcp_client or RemoteMCPClient()
    store = memory or MemoryStore()

    def retrieve_context(state: AgentState) -> dict:
        hits = (search or retrieve)(state["question"], k=5, min_score=minimum_score())
        return {
            "context": hits,
            "trace": _note(state, "retrieve_context", f"kept {len(hits)} chunks"),
        }

    def lookup_ticket_node(state: AgentState) -> dict:
        query = dict(state.get("ticket_query") or {})
        if query.get("ticket_id") is not None:
            tool = "get_incident"
            arguments = {"ticket_id": query["ticket_id"]}
        else:
            tool = "list_incidents"
            arguments = {
                key: query[key]
                for key in ("status", "category", "origin", "branch")
                if query.get(key)
            }
        result = run_tool(lambda: client.call_tool(tool, arguments), timeout=timeout)
        failed = not isinstance(result, dict) or not result.get("found")
        output = "ticket unavailable" if failed else format_tickets(result)
        return {
            "ticket_result": result if isinstance(result, dict) else None,
            "ticket_failed": failed,
            "trace": _note(state, "lookup_ticket", output),
        }

    def lookup_inventory_node(state: AgentState) -> dict:
        result = run_tool(
            lambda: client.call_tool("read_inventory", {"product": state.get("product") or ""}),
            timeout=timeout,
        )
        failed = not isinstance(result, dict) or not result.get("found")
        output = "inventory unavailable" if failed else format_products(result)
        return {
            "inventory_result": result if isinstance(result, dict) else None,
            "inventory_failed": failed,
            "trace": _note(state, "lookup_inventory", output),
        }

    def write_answer(state: AgentState) -> dict:
        question = state["question"]
        notes = []
        if state.get("use_ticket"):
            notes.append(
                TICKET_UNAVAILABLE
                if state.get("ticket_failed")
                else format_tickets(state.get("ticket_result") or {})
            )
        if state.get("use_inventory"):
            notes.append(
                INVENTORY_UNAVAILABLE
                if state.get("inventory_failed")
                else format_products(state.get("inventory_result") or {})
            )
        recalled = store.relevant(state.get("question") or "")
        if recalled:
            lines = "\n".join(f"- {row['fact']}" for row in recalled)
            question = f"Approved operational memory:\n{lines}\n\n{question}"
        if notes:
            question = f"{question}\n\n{isolate('tools', chr(10).join(notes))}"
        spoken, model_proposal, structured = parse_structured_reply(
            generate_answer(
                question,
                state.get("context") or [],
                complete=complete,
                memory_field=True,
            )
        )
        answer = _spoken(state, spoken)
        return {
            "answer": answer,
            "error": "",
            "model_proposal": model_proposal,
            "structured_reply": structured,
            "trace": _note(state, "generate_answer", answer),
        }

    def honest_answer(state: AgentState) -> dict:
        answer = _spoken(state, NOT_ENOUGH)
        return {
            "answer": answer,
            "error": "",
            "trace": _note(state, "honest_answer", answer),
        }

    def report_tools(state: AgentState) -> dict:
        parts = []
        if state.get("use_ticket"):
            parts.append(
                TICKET_UNAVAILABLE
                if state.get("ticket_failed")
                else format_tickets(state.get("ticket_result") or {})
            )
        if state.get("use_inventory"):
            parts.append(
                INVENTORY_UNAVAILABLE
                if state.get("inventory_failed")
                else format_products(state.get("inventory_result") or {})
            )
        answer = _spoken(state, " ".join(part for part in parts if part) or TICKET_UNAVAILABLE)
        return {
            "answer": answer,
            "error": "",
            "trace": _note(state, "report_tools", answer),
        }

    def screen_input(state: AgentState) -> dict:
        """Refuse a jailbreak or a personal task, and redirect casual talk, before any tool or model call."""
        if state.get("error"):
            return {
                "guard_stop": False,
                "trace": _note(state, "screen_input", "skipped"),
            }
        screened = screen_message(state.get("question") or "")
        if screened["action"] == "allow":
            return {
                "guard_stop": False,
                "trace": _note(state, "screen_input", "allowed"),
            }
        return {
            "answer": screened["answer"],
            "error": "",
            "guard_stop": True,
            "model_proposal": None,
            "structured_reply": False,
            "trace": _note(state, "screen_input", screened["name"]),
        }

    def route_after_screen(state: AgentState) -> str:
        if state.get("guard_stop"):
            return END
        return route_after_question(state)

    def screen_output(state: AgentState) -> dict:
        """Block a malformed reply, a leaked instruction, or a poisoned memory fact."""
        answer = str(state.get("answer") or "")
        verdict = check_output(answer)
        proposal = state.get("model_proposal") or None
        fact = str(proposal.get("fact") or "") if isinstance(proposal, dict) else ""
        fact_screen = screen_message(fact) if fact else {"action": "allow", "name": ""}
        fact_output = check_output(fact) if fact else {"action": "allow", "name": ""}
        blocked = (
            verdict["action"] != "allow"
            or fact_screen["action"] != "allow"
            or fact_output["action"] != "allow"
        )
        if not blocked:
            return {"trace": _note(state, "screen_output", "allowed")}
        name = verdict["name"] or fact_screen["name"] or fact_output["name"]
        spoken = verdict["answer"] if verdict["action"] != "allow" else answer
        return {
            "answer": spoken,
            "model_proposal": None,
            "structured_reply": True,
            "trace": _note(state, "screen_output", name),
        }

    def route_after_question(state: AgentState) -> str:
        message = state.get("question") or ""
        if classify_decision(message)["label"] not in {"approve", "reject", "edit"}:
            store.close_unanswered()
        thread = state.get("thread_id") or ""
        if state.get("error"):
            if store.pending(thread):
                return "resolve_proposal"
            return END
        if store.pending(thread):
            return "resolve_proposal"
        return "choose_sources"

    def route_after_resolve(state: AgentState) -> str:
        if state.get("stop_after_decision"):
            return END
        return "choose_sources"

    def resolve_proposal(state: AgentState) -> dict:
        thread = state.get("thread_id") or ""
        pending = store.pending(thread)
        message = state.get("question") or ""
        if not pending:
            return {
                "stop_after_decision": False,
                "trace": _note(state, "resolve_proposal", "no pending proposal"),
            }
        if not message.strip():
            store.log(
                thread_id=thread,
                proposal=pending["fact"],
                decision="reject",
                outcome="discarded because the user did not answer",
                originating_message=pending["originating_message"],
                decision_message="",
            )
            store.clear_pending(thread)
            return {
                "answer": REJECTED_REPLY,
                "error": "",
                "stop_after_decision": True,
                "memory_note": "",
                "trace": _note(state, "resolve_proposal", "discarded because the user did not answer"),
            }
        decision = classify_decision(message)
        label = decision["label"]
        origin = pending["originating_message"]
        if label == "unclear":
            store.log(
                thread_id=thread,
                proposal=pending["fact"],
                decision="reject",
                outcome="discarded because the reply was not a clear decision",
                originating_message=origin,
                decision_message=message,
            )
            store.clear_pending(thread)
            return {
                "stop_after_decision": False,
                "memory_note": "",
                "trace": _note(state, "resolve_proposal", "discarded"),
            }
        if label == "reject":
            store.log(
                thread_id=thread,
                proposal=pending["fact"],
                decision="reject",
                outcome="rejected",
                originating_message=origin,
                decision_message=message,
            )
            store.clear_pending(thread)
            note = REJECTED_REPLY
        elif label == "edit":
            try:
                store.write_memory(
                    decision["fact"],
                    why="The user edited the proposal.",
                    originating_message=origin,
                    decision="edit",
                )
            except MemoryRefusal as exc:
                outcome = f"refused: {exc}"
                note = FORBIDDEN_REPLY
            else:
                outcome = "stored"
                note = EDITED_REPLY
            store.log(
                thread_id=thread,
                proposal=pending["fact"],
                decision="edit",
                outcome=outcome,
                originating_message=origin,
                decision_message=message,
            )
            store.clear_pending(thread)
        else:
            try:
                store.write_memory(
                    pending["fact"],
                    why=pending["why"],
                    originating_message=origin,
                    decision="approve",
                )
            except MemoryRefusal as exc:
                outcome = f"refused: {exc}"
                note = FORBIDDEN_REPLY
            else:
                outcome = "stored"
                note = APPROVED_REPLY
            store.log(
                thread_id=thread,
                proposal=pending["fact"],
                decision="approve",
                outcome=outcome,
                originating_message=origin,
                decision_message=message,
            )
            store.clear_pending(thread)
        remainder = decision["remainder"]
        if remainder:
            return {
                "question": remainder,
                "memory_note": note,
                "stop_after_decision": False,
                "trace": _note(state, "resolve_proposal", f"{label} and continue"),
            }
        return {
            "answer": note,
            "error": "",
            "memory_note": note,
            "stop_after_decision": True,
            "trace": _note(state, "resolve_proposal", label),
        }

    def consider_memory(state: AgentState) -> dict:
        thread = state.get("thread_id") or ""
        answer = _spoken(state, state.get("answer") or "")
        if store.pending(thread):
            return {
                "answer": answer,
                "memory_proposal": None,
                "trace": _note(state, "consider_memory", "proposal already pending"),
            }
        if state.get("structured_reply"):
            proposal = state.get("model_proposal") or None
        else:
            proposal = proposal_for(state.get("question") or "", answer)
        if proposal is None:
            return {
                "answer": answer,
                "memory_proposal": None,
                "trace": _note(state, "consider_memory", "nothing to remember"),
            }
        if proposal["forbidden"]:
            store.log(
                thread_id=thread,
                proposal=proposal["fact"],
                decision="reject",
                outcome=f"refused: {proposal['why']}",
                originating_message=state.get("question") or "",
                decision_message="",
            )
            return {
                "answer": f"{answer} {FORBIDDEN_REPLY}".strip(),
                "memory_proposal": None,
                "trace": _note(state, "consider_memory", "forbidden"),
            }
        if any(fact_key(row["fact"]) == fact_key(proposal["fact"]) for row in store.read_memory()):
            return {
                "answer": answer,
                "memory_proposal": None,
                "trace": _note(state, "consider_memory", "already stored"),
            }
        store.propose(thread, proposal["fact"], proposal["why"], state.get("question") or "")
        spoken = f"{answer} {PROPOSAL_QUESTION} {proposal['fact']}".strip()
        return {
            "answer": spoken,
            "memory_proposal": {"fact": proposal["fact"], "why": proposal["why"]},
            "trace": _note(state, "consider_memory", "proposed"),
        }

    builder = StateGraph(AgentState)
    builder.add_node("receive_question", receive_question)
    builder.add_node("screen_input", screen_input)
    builder.add_node("resolve_proposal", resolve_proposal)
    builder.add_node("choose_sources", choose_sources)
    builder.add_node("lookup_ticket", lookup_ticket_node)
    builder.add_node("lookup_inventory", lookup_inventory_node)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("generate_answer", write_answer)
    builder.add_node("honest_answer", honest_answer)
    builder.add_node("report_tools", report_tools)
    builder.add_node("consider_memory", consider_memory)
    builder.add_node("screen_output", screen_output)
    builder.add_edge(START, "receive_question")
    builder.add_edge("receive_question", "screen_input")
    builder.add_conditional_edges(
        "screen_input",
        route_after_screen,
        {
            "resolve_proposal": "resolve_proposal",
            "choose_sources": "choose_sources",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "resolve_proposal",
        route_after_resolve,
        {"choose_sources": "choose_sources", END: END},
    )
    builder.add_conditional_edges(
        "choose_sources",
        route_after_plan,
        {
            "lookup_ticket": "lookup_ticket",
            "lookup_inventory": "lookup_inventory",
            "retrieve_context": "retrieve_context",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "lookup_ticket",
        route_after_ticket,
        {
            "lookup_inventory": "lookup_inventory",
            "retrieve_context": "retrieve_context",
            "report_tools": "report_tools",
        },
    )
    builder.add_conditional_edges(
        "lookup_inventory",
        route_after_inventory,
        {"retrieve_context": "retrieve_context", "report_tools": "report_tools"},
    )
    builder.add_conditional_edges(
        "retrieve_context",
        route_after_retrieve,
        {
            "generate_answer": "generate_answer",
            "report_tools": "report_tools",
            "honest_answer": "honest_answer",
        },
    )
    builder.add_edge("generate_answer", "screen_output")
    builder.add_edge("honest_answer", "screen_output")
    builder.add_edge("report_tools", "screen_output")
    builder.add_edge("screen_output", "consider_memory")
    builder.add_edge("consider_memory", END)
    return builder.compile(checkpointer=checkpointer or MemorySaver())


_compiled = None


def get_graph():
    """Return the one compiled graph used by the API."""
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


def run_agent(
    question: str,
    *,
    search=None,
    complete=None,
    thread_id: str | None = None,
    graph=None,
    mcp_client=None,
    tool_timeout: float | None = None,
    memory: MemoryStore | None = None,
) -> dict:
    """Run one question. The returned trace and checkpoints can be read after the run."""
    compiled = graph
    if compiled is None:
        custom = any(
            item is not None
            for item in (search, complete, mcp_client, tool_timeout, memory)
        )
        compiled = (
            build_graph(
                search=search,
                complete=complete,
                mcp_client=mcp_client,
                tool_timeout=tool_timeout,
                memory=memory,
            )
            if custom
            else get_graph()
        )
    thread = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread}}
    final = compiled.invoke(
        {
            "question": question,
            "context": [],
            "answer": "",
            "error": "",
            "trace": [],
            "thread_id": thread,
            "memory_note": "",
            "stop_after_decision": False,
            "structured_reply": False,
            "model_proposal": None,
            "guard_stop": False,
        },
        config,
    )
    history = list(compiled.get_state_history(config))
    result = dict(final)
    result["thread_id"] = thread
    result["checkpoints"] = [
        {
            "next": list(snap.next),
            "trace": list((snap.values or {}).get("trace") or []),
        }
        for snap in history
    ]
    return result
