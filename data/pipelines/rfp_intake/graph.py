"""Dedicated intake graph. It is not part of the support-agent graph."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from data.pipelines.rfp_intake.analyze import (
    classify_document,
    extract_metadata,
    select_departments,
    synthesize,
    work_department,
)


class IntakeState(TypedDict, total=False):
    markdown: str
    is_rfp: bool
    discard_reason: str
    metadata: dict
    departments: list[str]
    unknown_departments: list[str]
    sections: list[dict]
    summary: str
    open_questions: list[str]
    conflicts: list[str]
    handoff: dict


def _worker(department_id: str):
    def run(state: IntakeState) -> dict:
        if department_id not in (state.get("departments") or []):
            return {}
        section = work_department(
            department_id,
            state.get("markdown") or "",
            state.get("metadata") or {},
        )
        sections = [dict(item) for item in state.get("sections") or []]
        sections.append(section)
        return {"sections": sections}

    return run


def build_graph():
    """Classify, then orchestrate the briefing departments, then synthesize."""

    def classify(state: IntakeState) -> dict:
        decision = classify_document(state.get("markdown") or "")
        return {
            "is_rfp": decision["is_rfp"],
            "discard_reason": "" if decision["is_rfp"] else decision["reason"],
            "sections": [],
        }

    def route_after_classify(state: IntakeState) -> str:
        if state.get("is_rfp"):
            return "extract_metadata"
        return END

    def extract(state: IntakeState) -> dict:
        return {"metadata": extract_metadata(state.get("markdown") or "")}

    def orchestrate(state: IntakeState) -> dict:
        departments, unknown = select_departments(state.get("markdown") or "")
        metadata = dict(state.get("metadata") or {})
        metadata["departments_needed"] = departments
        return {
            "departments": departments,
            "unknown_departments": unknown,
            "metadata": metadata,
        }

    def compose(state: IntakeState) -> dict:
        metadata = state.get("metadata") or {}
        sections = state.get("sections") or []
        unknown = state.get("unknown_departments") or []
        report = synthesize(metadata, sections, unknown)
        handoff = {
            "status": "intake_complete",
            "metadata": metadata,
            "key_aspects": {
                section["department_id"]: section["key_aspects"] for section in sections
            },
            "contacts": {
                section["department_id"]: section["contact_name"] for section in sections
            },
            "summary": report["summary"],
            "open_questions": report["open_questions"],
            "conflicts": report["conflicts"],
        }
        return {
            "summary": report["summary"],
            "open_questions": report["open_questions"],
            "conflicts": report["conflicts"],
            "handoff": handoff,
        }

    builder = StateGraph(IntakeState)
    builder.add_node("classify", classify)
    builder.add_node("extract_metadata", extract)
    builder.add_node("orchestrate", orchestrate)
    builder.add_node("work_marketing", _worker("marketing"))
    builder.add_node("work_operaciones", _worker("operaciones"))
    builder.add_node("work_procurement", _worker("procurement"))
    builder.add_node("work_training", _worker("training"))
    builder.add_node("synthesize", compose)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify",
        route_after_classify,
        {"extract_metadata": "extract_metadata", END: END},
    )
    builder.add_edge("extract_metadata", "orchestrate")
    builder.add_edge("orchestrate", "work_marketing")
    builder.add_edge("work_marketing", "work_operaciones")
    builder.add_edge("work_operaciones", "work_procurement")
    builder.add_edge("work_procurement", "work_training")
    builder.add_edge("work_training", "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()


_compiled = None


def analyze_rfp(markdown: str) -> dict:
    """Run the intake graph on Markdown that was converted from the PDF."""
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return dict(_compiled.invoke({"markdown": markdown, "sections": []}))
