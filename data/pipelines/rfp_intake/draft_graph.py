"""Part 2 graph. Each department drafts on its own, then three evaluators run together."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from data.pipelines.rfp_intake.analyze import DEPARTMENTS
from data.pipelines.rfp_intake.draft import (
    MAX_ATTEMPTS,
    above_ceo_threshold,
    department_slice,
)


class SectionState(TypedDict, total=False):
    department_id: str
    metadata: dict
    key_aspects: list[str]
    open_questions: list[str]
    contact_name: str
    feedback: str
    draft: str
    iteration: int
    max_attempts: int
    readability: dict
    relevance: dict
    compliance: dict
    evaluation: dict


class TicketDraftState(TypedDict, total=False):
    handoff: dict
    max_attempts: int
    sections: Annotated[list[dict], operator.add]
    drafted: dict


_phase_hook = None
_department_graphs: dict = {}
_ticket_graph = None


def set_phase_hook(hook) -> None:
    """The service uses this to mark under_evaluation while evaluators are running."""
    global _phase_hook
    _phase_hook = hook


def _notify(phase: str) -> None:
    if _phase_hook is not None:
        _phase_hook(phase)


def _compile_department(department_id: str):
    def generate(state: SectionState) -> dict:
        import data.pipelines.rfp_intake.draft as draft_mod

        writer = getattr(draft_mod, f"generate_{department_id}")
        return {
            "draft": writer(state),
            "iteration": int(state.get("iteration") or 0) + 1,
        }

    def readability(state: SectionState) -> dict:
        import data.pipelines.rfp_intake.draft as draft_mod

        _notify("under_evaluation")
        return {"readability": draft_mod.evaluate_readability(state.get("draft") or "")}

    def relevance(state: SectionState) -> dict:
        import data.pipelines.rfp_intake.draft as draft_mod

        _notify("under_evaluation")
        return {
            "relevance": draft_mod.evaluate_relevance(
                state.get("draft") or "",
                list(state.get("key_aspects") or []),
            )
        }

    def compliance(state: SectionState) -> dict:
        import data.pipelines.rfp_intake.draft as draft_mod

        _notify("under_evaluation")
        return {"compliance": draft_mod.evaluate_compliance(state.get("draft") or "")}

    def join(state: SectionState) -> dict:
        import data.pipelines.rfp_intake.draft as draft_mod

        result = draft_mod.combine_evaluation(
            department_id,
            state.get("readability") or {},
            state.get("relevance") or {},
            state.get("compliance") or {},
        )
        return {"evaluation": result, "feedback": result["feedback_for_generator"]}

    def route(state: SectionState) -> str:
        evaluation = state.get("evaluation") or {}
        if evaluation.get("overall_pass"):
            return END
        if int(state.get("iteration") or 0) >= int(state.get("max_attempts") or MAX_ATTEMPTS):
            return END
        return "generate"

    builder = StateGraph(SectionState)
    builder.add_node("generate", generate)
    builder.add_node("readability", readability)
    builder.add_node("relevance", relevance)
    builder.add_node("compliance", compliance)
    builder.add_node("join_evaluation", join, defer=True)
    builder.add_edge(START, "generate")
    builder.add_edge("generate", "readability")
    builder.add_edge("generate", "relevance")
    builder.add_edge("generate", "compliance")
    builder.add_edge("readability", "join_evaluation")
    builder.add_edge("relevance", "join_evaluation")
    builder.add_edge("compliance", "join_evaluation")
    builder.add_conditional_edges(
        "join_evaluation",
        route,
        {"generate": "generate", END: END},
    )
    return builder.compile()


def department_graph(department_id: str):
    if department_id not in _department_graphs:
        _department_graphs[department_id] = _compile_department(department_id)
    return _department_graphs[department_id]


def run_department(handoff: dict, department_id: str, max_attempts: int) -> dict:
    """Run one department graph. The other departments are separate graphs."""
    payload = department_slice(handoff, department_id)
    payload["iteration"] = 0
    payload["max_attempts"] = max_attempts
    result = dict(department_graph(department_id).invoke(payload))
    evaluation = result.get("evaluation") or {}
    approval = "pending" if evaluation.get("overall_pass") else "needs_human_review"
    return {
        "department_id": department_id,
        "contact_name": payload["contact_name"],
        "draft_content": result.get("draft") or "",
        "evaluation": evaluation,
        "approval_status": approval,
        "iterations": int(result.get("iteration") or 0),
    }


def _department_node(department_id: str):
    def run(state: TicketDraftState) -> dict:
        handoff = state.get("handoff") or {}
        if department_id not in (handoff.get("key_aspects") or {}):
            return {"sections": []}
        section = run_department(
            handoff,
            department_id,
            int(state.get("max_attempts") or MAX_ATTEMPTS),
        )
        return {"sections": [section]}

    return run


def _assemble(state: TicketDraftState) -> dict:
    handoff = dict(state.get("handoff") or {})
    questions = handoff.pop("section_questions", None)
    order = list(DEPARTMENTS)
    sections = sorted(
        state.get("sections") or [],
        key=lambda section: order.index(section["department_id"]),
    )
    needs_review = any(section["approval_status"] == "needs_human_review" for section in sections)
    status = "needs_human_review" if needs_review else "under_evaluation"
    handoff["status"] = status
    handoff["sections"] = [
        {
            "department_id": section["department_id"],
            "draft_content": section["draft_content"],
            "evaluation": section["evaluation"],
            "approval_status": section["approval_status"],
            "iterations": section["iterations"],
        }
        for section in sections
    ]
    budget = str((handoff.get("metadata") or {}).get("budget_range") or "")
    handoff["ceo_approval_required"] = above_ceo_threshold(budget)
    if questions is not None:
        handoff.pop("section_questions", None)
    return {"drafted": {"status": status, "sections": sections, "handoff": handoff}}


def build_ticket_graph():
    builder = StateGraph(TicketDraftState)
    for department_id in DEPARTMENTS:
        builder.add_node(f"draft_{department_id}", _department_node(department_id))
    builder.add_node("assemble", _assemble, defer=True)
    for department_id in DEPARTMENTS:
        builder.add_edge(START, f"draft_{department_id}")
        builder.add_edge(f"draft_{department_id}", "assemble")
    builder.add_edge("assemble", END)
    return builder.compile()


def draft_from_handoff(handoff: dict, *, max_attempts: int = MAX_ATTEMPTS) -> dict:
    """Draft every department on the Part 1 handoff. The PDF is not read."""
    global _ticket_graph
    if _ticket_graph is None:
        _ticket_graph = build_ticket_graph()
    result = dict(
        _ticket_graph.invoke(
            {
                "handoff": handoff,
                "max_attempts": max_attempts,
                "sections": [],
            }
        )
    )
    return dict(result.get("drafted") or {})
