"""Per-department approval graph. A pause is a checkpoint, not a restart."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from data.pipelines.rfp_intake.approval import (
    apply_human_decision,
    log_step,
    offer_for_section,
    run_arbitration_rounds,
    thread_id,
    validate_decision,
)

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT_PATH = ROOT / "data" / "agent_memory" / "rfp_approval.sqlite"

_savers: dict[str, SqliteSaver] = {}
_department_graphs: dict[int, object] = {}
_arbitration_graphs: dict[int, object] = {}


class ApprovalState(TypedDict, total=False):
    ticket_id: str
    department_id: str
    owner: str
    draft_content: str
    evaluation: dict
    open_questions: list
    offered: dict
    decision: str
    approval_status: str
    approver: str
    approved_at: str
    approval_rounds: int
    limit_reached: bool
    trace: list


class ArbitrationState(TypedDict, total=False):
    sections: list
    metadata: dict
    ceo_approved: bool
    conflicts: list
    rounds: int
    applied: list
    trace: list


def get_saver(path: Path | None = None) -> SqliteSaver:
    """Persist the pause in SQLite. Memory is not the checkpoint outside a test."""
    target = Path(path or CHECKPOINT_PATH)
    key = str(target)
    if key not in _savers:
        target.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(target), check_same_thread=False)
        saver = SqliteSaver(connection)
        saver.setup()
        _savers[key] = saver
    return _savers[key]


def _config(ticket_id: str, department_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id(ticket_id, department_id)}}


def _department_graph(saver: SqliteSaver):
    key = id(saver)
    if key in _department_graphs:
        return _department_graphs[key]

    def offer(state: ApprovalState) -> dict:
        offered = offer_for_section(state)
        trace = log_step(
            state.get("trace"),
            "offer_approval",
            {"department_id": state.get("department_id")},
            offered,
        )
        return {"offered": offered, "trace": trace}

    def await_decision(state: ApprovalState) -> dict:
        decision = interrupt(state.get("offered") or {})
        trace = log_step(
            state.get("trace"),
            "await_decision",
            state.get("offered") or {},
            {"decision": decision},
        )
        return {"decision": decision, "trace": trace}

    def apply_decision(state: ApprovalState) -> dict:
        decision = validate_decision(str(state.get("decision") or ""))
        result = apply_human_decision(state, decision)
        trace = log_step(
            state.get("trace"),
            "apply_decision",
            {"decision": decision, "department_id": state.get("department_id")},
            dict(result),
        )
        result["trace"] = trace
        return result

    def route(state: ApprovalState) -> str:
        if state.get("approval_status") == "pending" and state.get("decision") == "request_changes":
            return "offer_approval"
        return END

    builder = StateGraph(ApprovalState)
    builder.add_node("offer_approval", offer)
    builder.add_node("await_decision", await_decision)
    builder.add_node("apply_decision", apply_decision)
    builder.add_edge(START, "offer_approval")
    builder.add_edge("offer_approval", "await_decision")
    builder.add_edge("await_decision", "apply_decision")
    builder.add_conditional_edges("apply_decision", route, {"offer_approval": "offer_approval", END: END})
    compiled = builder.compile(checkpointer=saver)
    _department_graphs[key] = compiled
    return compiled


def _arbitration_graph(saver: SqliteSaver):
    key = id(saver)
    if key in _arbitration_graphs:
        return _arbitration_graphs[key]

    def arbitrate(state: ArbitrationState) -> dict:
        result = run_arbitration_rounds(
            list(state.get("sections") or []),
            dict(state.get("metadata") or {}),
            bool(state.get("ceo_approved")),
        )
        return result

    builder = StateGraph(ArbitrationState)
    builder.add_node("arbitrate", arbitrate)
    builder.add_edge(START, "arbitrate")
    builder.add_edge("arbitrate", END)
    compiled = builder.compile(checkpointer=saver)
    _arbitration_graphs[key] = compiled
    return compiled


def _snapshot(ticket_id: str, department_id: str, saver: SqliteSaver | None = None):
    graph = _department_graph(saver or get_saver())
    return graph.get_state(_config(ticket_id, department_id))


def is_interrupted(ticket_id: str, department_id: str, saver: SqliteSaver | None = None) -> bool:
    snapshot = _snapshot(ticket_id, department_id, saver)
    if not snapshot.next:
        return False
    return "await_decision" in snapshot.next


def read_approval(ticket_id: str, department_id: str, saver: SqliteSaver | None = None) -> dict:
    snapshot = _snapshot(ticket_id, department_id, saver)
    return dict(snapshot.values or {})


def start_department(ticket_id: str, section: dict, saver: SqliteSaver | None = None) -> dict:
    """Run one department until its own approval pause."""
    graph = _department_graph(saver or get_saver())
    graph.invoke(
        {
            "ticket_id": ticket_id,
            "department_id": section["department_id"],
            "owner": section.get("owner") or section.get("contact_name") or "",
            "draft_content": section.get("draft_content") or "",
            "evaluation": section.get("evaluation") or {},
            "open_questions": list(section.get("open_questions") or []),
            "approval_status": "pending",
            "approval_rounds": 0,
            "trace": [],
        },
        _config(ticket_id, section["department_id"]),
    )
    return read_approval(ticket_id, section["department_id"], saver)


def resume_department(ticket_id: str, department_id: str, decision: str, saver: SqliteSaver | None = None) -> dict:
    """Continue that department's thread from the pause. Other threads stay where they are."""
    cleaned = validate_decision(decision)
    if not is_interrupted(ticket_id, department_id, saver):
        raise ValueError("That department is not waiting for a decision.")
    graph = _department_graph(saver or get_saver())
    graph.invoke(Command(resume=cleaned), _config(ticket_id, department_id))
    return read_approval(ticket_id, department_id, saver)


def run_arbitration(ticket_id: str, sections: list[dict], metadata: dict, ceo_approved: bool = False, saver: SqliteSaver | None = None) -> dict:
    """One arbitration thread for the ticket. It does not approve a department."""
    graph = _arbitration_graph(saver or get_saver())
    config = _config(ticket_id, "arbitration")
    graph.invoke(
        {"sections": sections, "metadata": metadata, "ceo_approved": ceo_approved, "trace": []},
        config,
    )
    snapshot = graph.get_state(config)
    return dict(snapshot.values or {})
