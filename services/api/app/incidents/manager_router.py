"""Managed incidents. Responses are records or plain field errors, never stack traces."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from packages.shared.incident_validation import (  # noqa: E402
    BRANCH_VALUES,
    MANAGER_CATEGORIES,
    MANAGER_ORIGINS,
    MANAGER_STATUSES,
)

from app.auth.deps import get_current_user  # noqa: E402
from app.incidents.service import (  # noqa: E402
    change_status,
    create_incident,
    creation_error,
    filter_error,
    get_incident,
    list_incidents,
    status_change_error,
    summary,
    to_public,
)
from app.inventory.db import get_inventory_session  # noqa: E402

router = APIRouter(
    prefix="/api/incidents",
    tags=["incident-manager"],
    dependencies=[Depends(get_current_user)],
)


def _field_error(field: str, detail: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"field": field, "detail": detail})


@router.get("/summary")
def incident_summary(session: Session = Depends(get_inventory_session)) -> dict:
    return summary(session)


@router.get("")
def incident_list(
    status: str | None = None,
    origin: str | None = None,
    branch: str | None = None,
    category: str | None = None,
    session: Session = Depends(get_inventory_session),
):
    checks = (
        filter_error("status", status, MANAGER_STATUSES),
        filter_error("origin", origin, MANAGER_ORIGINS),
        filter_error("branch", branch, BRANCH_VALUES),
        filter_error("category", category, MANAGER_CATEGORIES),
    )
    for problem in checks:
        if problem:
            return _field_error(*problem)
    rows = list_incidents(
        session,
        status=status or None,
        origin=origin or None,
        branch=branch or None,
        category=category or None,
    )
    return [to_public(row) for row in rows]


@router.get("/{incident_id}")
def incident_detail(incident_id: int, session: Session = Depends(get_inventory_session)):
    row = get_incident(session, incident_id)
    if row is None:
        return _field_error("id", "No incident with that id was found.", 404)
    return to_public(row)


@router.post("", status_code=201)
def incident_create(body: dict, session: Session = Depends(get_inventory_session)):
    problem = creation_error(body)
    if problem:
        return _field_error(*problem)
    return to_public(create_incident(session, body))


@router.patch("/{incident_id}/status")
def incident_status(
    incident_id: int,
    body: dict,
    session: Session = Depends(get_inventory_session),
):
    row = get_incident(session, incident_id)
    if row is None:
        return _field_error("id", "No incident with that id was found.", 404)
    problem = status_change_error(row.status, body)
    if problem:
        return _field_error(*problem)
    updated = change_status(session, row, str(body["status"]).strip())
    return to_public(updated)
