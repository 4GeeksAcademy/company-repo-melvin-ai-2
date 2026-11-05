"""Compiled support-agent graph.

Each node does one job. Retrieval and answer generation stay in data.pipelines.rag.
`query()` is not used here, because it searches and writes the answer together.
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

EMPTY_QUESTION = "Enter a question."


class AgentState(TypedDict, total=False):
    """Only the fields the next node needs. This is not a conversation history."""

    question: str
    context: list[dict]
    answer: str
    error: str
    trace: list[dict]


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


def route_after_question(state: AgentState) -> str:
    if state.get("error"):
        return END
    return "retrieve_context"


def route_after_retrieve(state: AgentState) -> str:
    if state.get("context"):
        return "generate_answer"
    return "honest_answer"


def build_graph(*, search=None, complete=None, checkpointer=None):
    """Compile the graph. A missing node or edge fails here, before any run."""

    def retrieve_context(state: AgentState) -> dict:
        hits = (search or retrieve)(state["question"], k=5, min_score=minimum_score())
        kept = len(hits)
        return {
            "context": hits,
            "trace": _note(state, "retrieve_context", f"kept {kept} chunks"),
        }

    def write_answer(state: AgentState) -> dict:
        answer = generate_answer(
            state["question"],
            state.get("context") or [],
            complete=complete,
        )
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

    builder = StateGraph(AgentState)
    builder.add_node("receive_question", receive_question)
    builder.add_node("retrieve_context", retrieve_context)
    builder.add_node("generate_answer", write_answer)
    builder.add_node("honest_answer", honest_answer)
    builder.add_edge(START, "receive_question")
    builder.add_conditional_edges(
        "receive_question",
        route_after_question,
        {"retrieve_context": "retrieve_context", END: END},
    )
    builder.add_conditional_edges(
        "retrieve_context",
        route_after_retrieve,
        {"generate_answer": "generate_answer", "honest_answer": "honest_answer"},
    )
    builder.add_edge("generate_answer", END)
    builder.add_edge("honest_answer", END)
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
) -> dict:
    """Run one question. The returned trace and checkpoints can be read after the run."""
    compiled = graph
    if compiled is None:
        compiled = (
            build_graph(search=search, complete=complete)
            if search is not None or complete is not None
            else get_graph()
        )
    thread = thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread}}
    final = compiled.invoke(
        {"question": question, "context": [], "answer": "", "error": "", "trace": []},
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
