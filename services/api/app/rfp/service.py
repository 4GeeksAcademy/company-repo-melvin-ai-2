"""Save an uploaded PDF, then run the intake graph off the request."""

from __future__ import annotations

import json
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines.rfp_intake.analyze import DEPARTMENTS
from data.pipelines.rfp_intake.approval import (
    CEO_ID,
    CEO_OWNER,
    ceo_section,
    ready_for_document,
    render_final_document,
)
from data.pipelines.rfp_intake.approval_graph import (
    is_interrupted,
    read_approval,
    resume_department,
    run_arbitration,
    start_department,
)
from data.pipelines.rfp_intake.document import pdf_to_markdown, readability_metrics
from data.pipelines.rfp_intake.draft_graph import draft_from_handoff, set_phase_hook
from data.pipelines.rfp_intake.graph import analyze_rfp

from app.rfp.models import RfpDepartmentSection, RfpTicket

RAW_DIR = ROOT / "data" / "raw" / "rfp"


def create_ticket(session: Session, pdf_bytes: bytes) -> RfpTicket:
    """Store the PDF and open the ticket as analyzing. The graph runs afterward."""
    ticket_id = uuid.uuid4().hex
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{ticket_id}.pdf"
    path.write_bytes(pdf_bytes)
    now_row = RfpTicket(
        ticket_id=ticket_id,
        status="analyzing",
        raw_pdf_path=str(path),
    )
    session.add(now_row)
    session.commit()
    session.refresh(now_row)
    return now_row


def process_ticket(session: Session, ticket_id: str) -> RfpTicket:
    """Convert, classify, and either discard the ticket or finish intake."""
    row = session.get(RfpTicket, ticket_id)
    if row is None:
        raise LookupError(ticket_id)
    try:
        markdown = pdf_to_markdown(Path(row.raw_pdf_path))
        metrics = readability_metrics(markdown)
        result = analyze_rfp(markdown)
        row.flesch_kincaid = metrics["flesch_kincaid"]
        row.gunning_fog = metrics["gunning_fog"]
        if not result.get("is_rfp"):
            row.status = "discarded"
            row.discard_reason = str(result.get("discard_reason") or "")
            row.summary = row.discard_reason
            row.handoff_json = json.dumps(
                {"ticket_id": ticket_id, "status": "discarded", "reason": row.discard_reason}
            )
        else:
            _store_sections(session, row, result)
            row.status = "intake_complete"
        row.error_detail = ""
    except Exception as exc:
        row.error_detail = str(exc)[:500]
        row.status = "analyzing"
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _store_sections(session: Session, row: RfpTicket, result: dict) -> None:
    metadata = result.get("metadata") or {}
    row.client_name = str(metadata.get("client_name") or "")
    row.location = str(metadata.get("location") or "")
    row.service_type = str(metadata.get("service_type") or "")
    row.scope = str(metadata.get("scope") or "")
    row.deadline = str(metadata.get("deadline") or "")
    row.budget_range = str(metadata.get("budget_range") or "")
    departments = metadata.get("departments_needed") or result.get("departments") or []
    row.departments_needed = ",".join(departments)
    row.summary = str(result.get("summary") or "")
    row.open_questions = "\n".join(result.get("open_questions") or [])
    handoff = dict(result.get("handoff") or {})
    handoff["ticket_id"] = row.ticket_id
    row.handoff_json = json.dumps(handoff)
    for section in result.get("sections") or []:
        department_id = section["department_id"]
        session.add(
            RfpDepartmentSection(
                ticket_id=row.ticket_id,
                department_id=department_id,
                key_aspects="\n".join(section.get("key_aspects") or []),
                contact_name=section.get("contact_name") or DEPARTMENTS[department_id]["owner"],
                open_questions="\n".join(section.get("open_questions") or []),
            )
        )


def mark_drafting(session: Session, ticket_id: str) -> dict:
    """Move an intake_complete ticket to drafting before the graph runs."""
    row = session.get(RfpTicket, ticket_id)
    if row is None:
        raise LookupError(ticket_id)
    if row.status != "intake_complete":
        raise ValueError("Drafting starts from an intake_complete ticket.")
    row.status = "drafting"
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return ticket_payload(session, row)


def process_draft(session: Session, ticket_id: str) -> RfpTicket:
    """Draft from the Part 1 handoff. The PDF is not opened again."""
    row = session.get(RfpTicket, ticket_id)
    if row is None:
        raise LookupError(ticket_id)
    if row.status not in {"intake_complete", "drafting"}:
        raise ValueError("Drafting starts from an intake_complete ticket.")
    try:
        handoff = json.loads(row.handoff_json) if row.handoff_json else {}
    except json.JSONDecodeError as exc:
        raise ValueError("The Part 1 handoff is missing.") from exc
    if not handoff.get("key_aspects"):
        raise ValueError("The Part 1 handoff is missing.")
    sections = session.exec(
        select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == ticket_id)
    ).all()
    handoff["section_questions"] = {
        section.department_id: [line for line in section.open_questions.splitlines() if line]
        for section in sections
    }
    _mark(session, ticket_id, "drafting")
    lock = threading.Lock()

    def publish(phase: str) -> None:
        if phase != "under_evaluation":
            return
        with lock:
            _mark(session, ticket_id, "under_evaluation", only_from="drafting")

    set_phase_hook(publish)
    try:
        drafted = draft_from_handoff(handoff)
    except Exception as exc:
        set_phase_hook(None)
        failed = session.get(RfpTicket, ticket_id)
        if failed is not None:
            failed.error_detail = str(exc)[:500]
            failed.updated_at = datetime.now(timezone.utc)
            session.add(failed)
            session.commit()
        raise
    finally:
        set_phase_hook(None)
    session.expire_all()
    row = session.get(RfpTicket, ticket_id)
    stored = {
        section.department_id: section
        for section in session.exec(
            select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == ticket_id)
        ).all()
    }
    for section in drafted.get("sections") or []:
        current = stored.get(section["department_id"])
        if current is None:
            current = RfpDepartmentSection(
                ticket_id=ticket_id,
                department_id=section["department_id"],
                contact_name=section.get("contact_name") or "",
            )
            session.add(current)
        current.draft_content = section.get("draft_content") or ""
        current.evaluation_results = json.dumps(section.get("evaluation") or {})
        current.approval_status = section.get("approval_status") or ""
        current.iterations = int(section.get("iterations") or 0)
        if section.get("contact_name"):
            current.contact_name = section["contact_name"]
    row.status = str(drafted.get("status") or "under_evaluation")
    row.handoff_json = json.dumps(drafted.get("handoff") or {})
    row.error_detail = ""
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _mark(session: Session, ticket_id: str, status: str, only_from: str | None = None) -> None:
    """Write the ticket status on its own connection so a parallel evaluator can publish it."""
    with Session(session.get_bind()) as extra:
        current = extra.get(RfpTicket, ticket_id)
        if current is None:
            return
        if only_from is not None and current.status != only_from:
            return
        if current.status == status:
            return
        current.status = status
        current.updated_at = datetime.now(timezone.utc)
        extra.add(current)
        extra.commit()


def begin_approval(session: Session, ticket_id: str) -> RfpTicket:
    """Pause each department for a signature. The pause is stored in SQLite."""
    row = session.get(RfpTicket, ticket_id)
    if row is None:
        raise LookupError(ticket_id)
    if row.status not in {"under_evaluation", "needs_human_review"}:
        raise ValueError("Approval starts after the department drafts are ready.")
    try:
        handoff = json.loads(row.handoff_json) if row.handoff_json else {}
    except json.JSONDecodeError as exc:
        raise ValueError("The Part 2 handoff is missing.") from exc
    stored = _sections_by_id(session, ticket_id)
    payload = [_section_dict(section) for section in stored.values() if section.draft_content]
    if not payload:
        raise ValueError("Approval starts after the department drafts are ready.")
    metadata = dict(handoff.get("metadata") or {})
    if not metadata and row.budget_range:
        metadata = {"budget_range": row.budget_range, "client_name": row.client_name}
    arbitration = run_arbitration(ticket_id, payload, metadata, False)
    revised = {section["department_id"]: section for section in arbitration.get("sections") or payload}
    for department_id, section in revised.items():
        current = stored.get(department_id)
        if current is not None:
            current.draft_content = section.get("draft_content") or current.draft_content
    if any(conflict.get("trigger_id") == "ceo-threshold" for conflict in arbitration.get("conflicts") or []):
        if CEO_ID not in stored:
            ceo = ceo_section(metadata or {"budget_range": row.budget_range})
            current = RfpDepartmentSection(
                ticket_id=ticket_id,
                department_id=CEO_ID,
                contact_name=CEO_OWNER,
                draft_content=ceo["draft_content"],
                approval_status="pending",
            )
            session.add(current)
            stored[CEO_ID] = current
            revised[CEO_ID] = ceo
    session.commit()
    for department_id, section in revised.items():
        start_department(
            ticket_id,
            {
                "department_id": department_id,
                "owner": section.get("owner") or section.get("contact_name") or _owner(department_id),
                "contact_name": section.get("contact_name") or _owner(department_id),
                "draft_content": section.get("draft_content") or "",
                "evaluation": section.get("evaluation") or _evaluation(
                    stored[department_id].evaluation_results if department_id in stored else ""
                ) or {},
                "open_questions": section.get("open_questions") or [],
            },
        )
    row = session.get(RfpTicket, ticket_id)
    row.status = "waiting_for_approval"
    handoff["arbitration"] = {
        "rounds": arbitration.get("rounds") or 0,
        "applied": arbitration.get("applied") or [],
        "conflicts": arbitration.get("conflicts") or [],
    }
    handoff["ticket_id"] = ticket_id
    row.handoff_json = json.dumps(handoff)
    row.trace_json = json.dumps(_collect_trace(ticket_id, list(revised.values())))
    row.error_detail = ""
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def resume_approval(session: Session, ticket_id: str, department_id: str, decision: str) -> RfpTicket:
    """Continue one department. A rejection leaves the final document unwritten."""
    row = session.get(RfpTicket, ticket_id)
    if row is None:
        raise LookupError(ticket_id)
    if row.status != "waiting_for_approval":
        raise ValueError("That ticket is not waiting for approval.")
    state = resume_department(ticket_id, department_id, decision)
    current = _sections_by_id(session, ticket_id).get(department_id)
    if current is None:
        raise LookupError(department_id)
    current.approval_status = str(state.get("approval_status") or "")
    current.approver = str(state.get("approver") or "")
    current.approved_at = str(state.get("approved_at") or "")
    current.decision = str(state.get("decision") or "")
    current.approval_rounds = int(state.get("approval_rounds") or 0)
    if state.get("draft_content"):
        current.draft_content = state["draft_content"]
    try:
        handoff = json.loads(row.handoff_json) if row.handoff_json else {}
    except json.JSONDecodeError:
        handoff = {}
    metadata = dict(handoff.get("metadata") or {})
    sections = [_section_dict(section) for section in _sections_by_id(session, ticket_id).values()]
    for section in sections:
        if section["department_id"] == department_id:
            section["approval_status"] = current.approval_status
            section["approver"] = current.approver
    if ready_for_document(sections, metadata):
        generated_at = datetime.now(timezone.utc).isoformat()
        row.final_document = render_final_document(row.client_name, sections, metadata, generated_at)
        row.status = "done"
        handoff["final_document"] = {
            "ticket_id": ticket_id,
            "generated_at": generated_at,
            "total_estimated_value": metadata.get("budget_range") or "",
        }
    else:
        row.status = "waiting_for_approval"
        row.final_document = ""
    handoff["ticket_id"] = ticket_id
    row.handoff_json = json.dumps(handoff)
    row.trace_json = json.dumps(_collect_trace(ticket_id, sections))
    row.updated_at = datetime.now(timezone.utc)
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _owner(department_id: str) -> str:
    if department_id == CEO_ID:
        return CEO_OWNER
    return DEPARTMENTS.get(department_id, {}).get("owner", "")


def _sections_by_id(session: Session, ticket_id: str) -> dict:
    rows = session.exec(
        select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == ticket_id)
    ).all()
    return {row.department_id: row for row in rows}


def _section_dict(section: RfpDepartmentSection) -> dict:
    return {
        "department_id": section.department_id,
        "owner": section.contact_name or _owner(section.department_id),
        "contact_name": section.contact_name or _owner(section.department_id),
        "draft_content": section.draft_content,
        "evaluation": _evaluation(section.evaluation_results) or {},
        "open_questions": [line for line in section.open_questions.splitlines() if line],
        "approval_status": section.approval_status,
        "approver": section.approver,
    }


def _collect_trace(ticket_id: str, sections: list[dict]) -> list:
    entries = []
    department_ids = ["arbitration"] + [section["department_id"] for section in sections]
    for department_id in department_ids:
        try:
            if department_id == "arbitration":
                from data.pipelines.rfp_intake.approval_graph import _arbitration_graph, _config, get_saver

                snapshot = _arbitration_graph(get_saver()).get_state(_config(ticket_id, "arbitration"))
                values = dict(snapshot.values or {})
            else:
                values = read_approval(ticket_id, department_id)
        except Exception:
            continue
        entries.extend(values.get("trace") or [])
    return entries


def ticket_payload(session: Session, row: RfpTicket) -> dict:
    sections = session.exec(
        select(RfpDepartmentSection).where(RfpDepartmentSection.ticket_id == row.ticket_id)
    ).all()
    try:
        handoff = json.loads(row.handoff_json) if row.handoff_json else {}
    except json.JSONDecodeError:
        handoff = {}
    return {
        "ticket_id": row.ticket_id,
        "status": row.status,
        "client_name": row.client_name,
        "location": row.location,
        "service_type": row.service_type,
        "scope": row.scope,
        "deadline": row.deadline,
        "budget_range": row.budget_range,
        "departments_needed": [item for item in row.departments_needed.split(",") if item],
        "flesch_kincaid": row.flesch_kincaid,
        "gunning_fog": row.gunning_fog,
        "summary": row.summary,
        "open_questions": [line for line in row.open_questions.splitlines() if line],
        "discard_reason": row.discard_reason,
        "error_detail": row.error_detail,
        "final_document": row.final_document,
        "trace": _trace(row.trace_json),
        "sections": [
            {
                "department_id": section.department_id,
                "contact_name": section.contact_name,
                "key_aspects": [line for line in section.key_aspects.splitlines() if line],
                "open_questions": [line for line in section.open_questions.splitlines() if line],
                "draft_content": section.draft_content,
                "approval_status": section.approval_status,
                "iterations": section.iterations,
                "approver": section.approver,
                "approved_at": section.approved_at,
                "decision": section.decision,
                "approval_rounds": section.approval_rounds,
                "awaiting_decision": _awaiting(row.ticket_id, section.department_id),
                "evaluation": _evaluation(section.evaluation_results),
            }
            for section in sections
        ],
        "handoff": handoff,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def _trace(raw: str) -> list:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _awaiting(ticket_id: str, department_id: str) -> bool:
    try:
        return is_interrupted(ticket_id, department_id)
    except Exception:
        return False


def _evaluation(raw: str) -> dict | None:
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return parsed or None


def list_tickets(session: Session) -> list[RfpTicket]:
    rows = session.exec(select(RfpTicket)).all()
    return sorted(rows, key=lambda row: row.created_at, reverse=True)
