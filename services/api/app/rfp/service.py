"""Save an uploaded PDF, then run the intake graph off the request."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Session, select

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines.rfp_intake.analyze import DEPARTMENTS
from data.pipelines.rfp_intake.document import pdf_to_markdown, readability_metrics
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
        "sections": [
            {
                "department_id": section.department_id,
                "contact_name": section.contact_name,
                "key_aspects": [line for line in section.key_aspects.splitlines() if line],
                "open_questions": [line for line in section.open_questions.splitlines() if line],
            }
            for section in sections
        ],
        "handoff": handoff,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def list_tickets(session: Session) -> list[RfpTicket]:
    rows = session.exec(select(RfpTicket)).all()
    return sorted(rows, key=lambda row: row.created_at, reverse=True)
