"""Compiled support-agent graph.

Each node does one job. Retrieval and answer generation stay in data.pipelines.rag.
Ticket and inventory reads stay in services.agent.tools. `query()` is not used here.
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
from services.agent.tools import (
    INVENTORY_UNAVAILABLE,
    TICKET_UNAVAILABLE,
    TOOL_TIMEOUT_SECONDS,
    default_inventory_lookup,
    default_ticket_lookup,
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


def route_after_question(state: AgentState) -> str:
    if state.get("error"):
        return END
    return "choose_sources"


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
    ticket_lookup=None,
    inventory_lookup=None,
    tool_timeout: float | None = None,
):
    """Compile the graph. A missing node or edge fails here, before any run."""
    timeout = TOOL_TIMEOUT_SECONDS if tool_timeout is None else tool_timeout
    read_ticket = ticket_lookup or default_ticket_lookup
    read_inventory = inventory_lookup or default_inventory_lookup

    def retrieve_context(state: AgentState) -> dict:
        hits = (search or retrieve)(state["question"], k=5, min_score=minimum_score())
        return {
            "context": hits,
            "trace": _note(state, "retrieve_context", f"kept {len(hits)} chunks"),
        }

    def lookup_ticket_node(state: AgentState) -> dict:
        result = run_tool(lambda: read_ticket(state.get("ticket_query") or {}), timeout=timeout)
        failed = not isinstance(result, dict) or not result.get("found")
        output = "ticket unavailable" if failed else format_tickets(result)
        return {
            "ticket_result": result if isinstance(result, dict) else None,
            "ticket_failed": failed,
            "trace": _note(state, "lookup_ticket", output),
        }

    def lookup_inventory_node(state: AgentState) -> dict:
        result = run_tool(lambda: read_inventory(state.get("product") or ""), timeout=timeout)
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
        if notes:
            question = f"{question}\n\nLive records:\n" + "\n".join(notes)
        answer = generate_answer(question, state.get("context") or [], complete=complete)
        return {
            "answer": answer,
            "error": "",
            "trace": _note(state, "generate_answer", answer),
        }

    def honest_answer(state: AgentState) -> dict:
        return {
            "answer": NOT_ENOUGH,
            "error": "",
            "trace": _note(state, "honest_answer", NOT_ENOUGH),
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
        answer = " ".join(part for part in parts if part) or TICKET_UNAVAILABLE
        return {
            "answer": answer,
            "error": "",
            "trace": _note(state, "report_tools", answer),
        }

    builder = StateGraph(AgentState)
    builder.add_node("receive_question", receive_question)
    builder.add_node("choose_sources", choose_sources)
    builder.add_node("lookup_ticket", lookup_ticket_node)
    builder.add_node("lookup_inventory", lookup_inventory_node)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("generate_answer", write_answer)
    builder.add_node("honest_answer", honest_answer)
    builder.add_node("report_tools", report_tools)
    builder.add_edge(START, "receive_question")
    builder.add_conditional_edges(
        "receive_question",
        route_after_question,
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
    builder.add_edge("generate_answer", END)
    builder.add_edge("honest_answer", END)
    builder.add_edge("report_tools", END)
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
    ticket_lookup=None,
    inventory_lookup=None,
    tool_timeout: float | None = None,
) -> dict:
    """Run one question. The returned trace and checkpoints can be read after the run."""
    compiled = graph
    if compiled is None:
        custom = any(
            item is not None
            for item in (search, complete, ticket_lookup, inventory_lookup, tool_timeout)
        )
        compiled = (
            build_graph(
                search=search,
                complete=complete,
                ticket_lookup=ticket_lookup,
                inventory_lookup=inventory_lookup,
                tool_timeout=tool_timeout,
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
