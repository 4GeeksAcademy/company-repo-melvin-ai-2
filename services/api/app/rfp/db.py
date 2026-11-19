"""Create the RFP tables on the same Postgres engine as inventory."""

from __future__ import annotations

from sqlalchemy import inspect, text
from sqlmodel import SQLModel

from app.inventory.db import database_url, get_engine
from app.rfp import models as _models  # noqa: F401

_SECTION_COLUMNS = {
    "draft_content": "TEXT DEFAULT ''",
    "evaluation_results": "TEXT DEFAULT ''",
    "approval_status": "TEXT DEFAULT ''",
    "iterations": "INTEGER DEFAULT 0",
    "approver": "TEXT DEFAULT ''",
    "approved_at": "TEXT DEFAULT ''",
    "decision": "TEXT DEFAULT ''",
    "approval_rounds": "INTEGER DEFAULT 0",
}

_TICKET_COLUMNS = {
    "final_document": "TEXT DEFAULT ''",
    "trace_json": "TEXT DEFAULT ''",
}


def _add_missing(connection, table: str, present: set[str], columns: dict[str, str]) -> None:
    for name, ddl in columns.items():
        if name not in present:
            connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


def ensure_section_columns(engine=None) -> None:
    """Add later-part columns when an earlier table is already present."""
    bound = engine or get_engine()
    insp = inspect(bound)
    names = set(insp.get_table_names())
    with bound.begin() as connection:
        if "rfp_department_sections" in names:
            present = {column["name"] for column in insp.get_columns("rfp_department_sections")}
            _add_missing(connection, "rfp_department_sections", present, _SECTION_COLUMNS)
        if "rfp_tickets" in names:
            present = {column["name"] for column in insp.get_columns("rfp_tickets")}
            _add_missing(connection, "rfp_tickets", present, _TICKET_COLUMNS)


def init_rfp_db() -> str:
    if not database_url():
        return "skipped"
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    ensure_section_columns(engine)
    return "ready"
