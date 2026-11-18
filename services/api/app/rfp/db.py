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
}


def ensure_section_columns(engine=None) -> None:
    """Add Part 2 columns when the Part 1 table is already present."""
    bound = engine or get_engine()
    insp = inspect(bound)
    if "rfp_department_sections" not in insp.get_table_names():
        return
    present = {column["name"] for column in insp.get_columns("rfp_department_sections")}
    with bound.begin() as connection:
        for name, ddl in _SECTION_COLUMNS.items():
            if name not in present:
                connection.execute(
                    text(f"ALTER TABLE rfp_department_sections ADD COLUMN {name} {ddl}")
                )


def init_rfp_db() -> str:
    if not database_url():
        return "skipped"
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    ensure_section_columns(engine)
    return "ready"
