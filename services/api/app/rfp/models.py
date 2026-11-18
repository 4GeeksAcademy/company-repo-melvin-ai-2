"""SQLModel tables for RFP tickets. TinyDB is not the source of truth."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RfpTicket(SQLModel, table=True):
    __tablename__ = "rfp_tickets"

    ticket_id: str = Field(primary_key=True)
    status: str = Field(index=True)
    raw_pdf_path: str
    client_name: str = ""
    location: str = ""
    service_type: str = ""
    scope: str = ""
    deadline: str = ""
    budget_range: str = ""
    departments_needed: str = ""
    flesch_kincaid: Optional[float] = None
    gunning_fog: Optional[float] = None
    summary: str = ""
    handoff_json: str = ""
    open_questions: str = ""
    discard_reason: str = ""
    error_detail: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


class RfpDepartmentSection(SQLModel, table=True):
    __tablename__ = "rfp_department_sections"

    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: str = Field(foreign_key="rfp_tickets.ticket_id", index=True)
    department_id: str = Field(index=True)
    key_aspects: str = ""
    contact_name: str = ""
    open_questions: str = ""
    draft_content: str = ""
    evaluation_results: str = ""
    approval_status: str = ""
    iterations: int = 0
