"""Read and write managed incidents. Validation comes from packages.shared."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from sqlmodel import Session, select

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from packages.shared.incident_validation import (  # noqa: E402
    BRANCH_VALUES,
    MANAGER_CATEGORIES,
    MANAGER_ORIGINS,
    MANAGER_STATUSES,
    seed_record,
    transition_error,
    validate_incident_fields,
)

from app.incidents.models import IncidentRecord, utc_now  # noqa: E402


def to_public(row: IncidentRecord) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "category": row.category,
        "status": row.status,
        "origin": row.origin,
        "branch": row.branch,
        "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
    }


def create_incident(session: Session, payload: dict) -> IncidentRecord:
    now = utc_now()
    row = IncidentRecord(
        title=str(payload["title"]).strip(),
        description=str(payload["description"]).strip(),
        category=str(payload["category"]).strip(),
        status=str(payload["status"]).strip(),
        origin=str(payload["origin"]).strip(),
        branch=str(payload["branch"]).strip(),
        created_at=now,
        updated_at=now,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_incidents(
    session: Session,
    *,
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
) -> list[IncidentRecord]:
    statement = select(IncidentRecord)
    if status:
        statement = statement.where(IncidentRecord.status == status)
    if origin:
        statement = statement.where(IncidentRecord.origin == origin)
    if branch:
        statement = statement.where(IncidentRecord.branch == branch)
    if category:
        statement = statement.where(IncidentRecord.category == category)
    statement = statement.order_by(IncidentRecord.created_at.desc(), IncidentRecord.id.desc())
    return list(session.exec(statement).all())


def get_incident(session: Session, incident_id: int) -> IncidentRecord | None:
    return session.get(IncidentRecord, incident_id)


def change_status(session: Session, row: IncidentRecord, status: str) -> IncidentRecord:
    row.status = status
    row.updated_at = utc_now()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def _counts(rows: list[IncidentRecord], key: str, order: tuple[str, ...]) -> dict[str, int]:
    found = Counter(getattr(row, key) for row in rows)
    return {name: found.get(name, 0) for name in order}


def summary(session: Session) -> dict:
    rows = list(session.exec(select(IncidentRecord)).all())
    return {
        "total": len(rows),
        "by_status": _counts(rows, "status", MANAGER_STATUSES),
        "by_category": _counts(rows, "category", MANAGER_CATEGORIES),
        "by_origin": _counts(rows, "origin", MANAGER_ORIGINS),
        "by_branch": _counts(rows, "branch", BRANCH_VALUES),
    }


def filter_error(name: str, value: str | None, allowed: tuple[str, ...]) -> tuple[str, str] | None:
    if value is None or value == "":
        return None
    if value not in allowed:
        return name, f"Choose a valid {name}."
    return None


def insert_seed_row(session: Session, record: dict) -> bool:
    """Insert one transformed CSV row. Return False when that seed key is already stored."""
    existing = session.exec(
        select(IncidentRecord).where(IncidentRecord.seed_key == record["seed_key"])
    ).first()
    if existing is not None:
        return False
    session.add(IncidentRecord(**record))
    session.commit()
    return True


def load_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    text = path.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def seed_csv(session: Session, path: Path) -> tuple[int, int, list[str]]:
    """Load valid customer incidents. Returns inserted, already present, and console lines."""
    inserted = 0
    already = 0
    notes: list[str] = []
    for index, row in enumerate(load_csv_rows(path), start=2):
        record, reason = seed_record(row)
        label = (row.get("incident_id") or row.get("ticket_id") or f"row {index}").strip()
        if record is None:
            line = f"Skipped {label}: {reason}"
            notes.append(line)
            print(line)
            continue
        if insert_seed_row(session, record):
            inserted += 1
        else:
            already += 1
            line = f"Already loaded {label}"
            notes.append(line)
            print(line)
    return inserted, already, notes


def creation_error(payload: object) -> tuple[str, str] | None:
    if not isinstance(payload, dict):
        return "body", "Send the incident as a JSON object."
    return validate_incident_fields(payload)


def status_change_error(current: str, payload: object) -> tuple[str, str] | None:
    if not isinstance(payload, dict) or "status" not in payload:
        return "status", "Choose a valid status."
    nxt = payload.get("status")
    if not isinstance(nxt, str):
        return "status", "Choose a valid status."
    message = transition_error(current, nxt.strip())
    if message:
        return "status", message
    return None
