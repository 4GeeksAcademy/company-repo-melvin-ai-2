"""Incident and inventory work for the MCP tools.

These functions call the existing services. The support agent does not.
"""

from __future__ import annotations

import sys
from pathlib import Path

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


def change_ticket_status(session, ticket_id: int, status: str) -> dict:
    from app.incidents.service import change_status, get_incident, status_change_error, to_public

    row = get_incident(session, int(ticket_id))
    if row is None:
        raise ToolFailure(400, "That ticket was not found.")
    error = status_change_error(row.status, {"status": status})
    if error:
        _field, message = error
        raise ToolFailure(400, message)
    updated = change_status(session, row, status.strip())
    return {"found": True, "tickets": [_view(to_public(updated))]}


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
