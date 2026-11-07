"""Incident and inventory work for the MCP tools.

These functions call the existing services. The support agent does not.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (str(ROOT), str(API)):
    if path not in sys.path:
        sys.path.insert(0, path)

from packages.shared.incident_validation import (  # noqa: E402
    MANAGER_CATEGORIES,
    MANAGER_ORIGINS,
    MANAGER_STATUSES,
    BRANCH_VALUES,
)


class ToolFailure(Exception):
    """A tool rejected the call. `status` is the HTTP code the server returns."""

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def ensure_tables() -> None:
    from sqlmodel import SQLModel

    from app.incidents import models as _incidents  # noqa: F401
    from app.inventory.db import get_engine
    from app.inventory.models import Ingredient, IngredientEntry, IngredientExit  # noqa: F401

    SQLModel.metadata.create_all(get_engine())


def _view(row: dict) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "category": row["category"],
        "origin": row["origin"],
        "branch": row["branch"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def read_ticket(session, query: dict) -> dict:
    """One ticket, or the tickets that match the incident filters."""
    from app.incidents.service import get_incident, list_incidents, to_public

    ticket_id = query.get("ticket_id")
    if ticket_id is not None:
        row = get_incident(session, int(ticket_id))
        tickets = [_view(to_public(row))] if row is not None else []
    else:
        rows = list_incidents(
            session,
            status=query.get("status"),
            origin=query.get("origin"),
            branch=query.get("branch"),
            category=query.get("category"),
        )
        tickets = [_view(to_public(row)) for row in rows]
    return {"found": bool(tickets), "tickets": tickets}


def create_ticket(session, payload: dict) -> dict:
    from app.incidents.service import create_incident, creation_error, to_public

    error = creation_error(payload)
    if error:
        field, message = error
        raise ToolFailure(400, f"{field}: {message}")
    row = create_incident(session, payload)
    return {"found": True, "tickets": [_view(to_public(row))]}


def _send_status_patch(path: str, payload: dict) -> httpx.Response:
    """PATCH the Incidents Manager lifecycle route, not the whole incident."""
    base = os.environ.get("BRASALAND_API_URL", "").strip()
    if base:
        headers = {}
        token = os.environ.get("BRASALAND_API_TOKEN", "").strip()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            return httpx.patch(
                base.rstrip("/") + path,
                json=payload,
                headers=headers,
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            raise ToolFailure(503, "The incident status endpoint did not respond.") from exc

    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from app.auth.deps import get_current_user
    from app.incidents.manager_router import router as incident_manager_router

    app = FastAPI()
    app.include_router(incident_manager_router)
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 0,
        "email": "mcp@brasaland.com",
        "is_active": True,
    }
    with TestClient(app) as client:
        return client.patch(path, json=payload)


def _status_error(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "The status change was rejected."
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail.strip()
    return "The status change was rejected."


def change_ticket_status(ticket_id: int, status: str) -> dict:
    """Send PATCH /api/incidents/{id}/status and return the updated ticket."""
    path = f"/api/incidents/{int(ticket_id)}/status"
    payload = {"status": status.strip()}
    response = _send_status_patch(path, payload)
    if response.status_code >= 400:
        raise ToolFailure(response.status_code, _status_error(response))
    return {"found": True, "tickets": [_view(response.json())]}


def read_stock(session, product: str) -> dict:
    """Current stock is entries minus exits. Nothing is written."""
    from sqlmodel import select

    from app.inventory.models import Ingredient
    from app.inventory.stock import stock_by_ingredient_ids

    rows = list(session.exec(select(Ingredient).order_by(Ingredient.sku)).all())
    needle = (product or "").strip().lower()
    if needle:
        rows = [
            row
            for row in rows
            if needle in row.name.lower() or needle in row.sku.lower()
        ]
    stocks = stock_by_ingredient_ids(session, [row.id for row in rows if row.id])
    products = [
        {
            "id": row.id,
            "name": row.name,
            "sku": row.sku,
            "unit": row.unit,
            "current_stock": stocks.get(row.id, 0.0),
        }
        for row in rows
    ]
    return {"found": bool(products), "products": products}


def open_session():
    from sqlmodel import Session

    from app.inventory.db import get_engine

    ensure_tables()
    return Session(get_engine())


def allowed_filter(name: str, value: str | None) -> str | None:
    """Reject a list filter that is not one of the incident API values."""
    if value is None or value == "":
        return None
    allowed = {
        "status": MANAGER_STATUSES,
        "origin": MANAGER_ORIGINS,
        "category": MANAGER_CATEGORIES,
        "branch": BRANCH_VALUES,
    }[name]
    if value not in allowed:
        raise ToolFailure(400, f"Choose a valid {name}.")
    return value
