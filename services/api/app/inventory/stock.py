"""Chain-wide current_stock: SUM(entries) − SUM(exits). Not stored."""

from __future__ import annotations

from typing import Dict, Iterable

from sqlalchemy import func
from sqlmodel import Session, select

from app.inventory.models import IngredientEntry, IngredientExit


def stock_by_ingredient_ids(
    session: Session, ingredient_ids: Iterable[int]
) -> Dict[int, float]:
    ids = list(dict.fromkeys(ingredient_ids))
    if not ids:
        return {}

    inbound = dict(
        session.exec(
            select(
                IngredientEntry.ingredient_id,
                func.coalesce(func.sum(IngredientEntry.quantity), 0.0),
            )
            .where(IngredientEntry.ingredient_id.in_(ids))
            .group_by(IngredientEntry.ingredient_id)
        ).all()
    )
    outbound = dict(
        session.exec(
            select(
                IngredientExit.ingredient_id,
                func.coalesce(func.sum(IngredientExit.quantity), 0.0),
            )
            .where(IngredientExit.ingredient_id.in_(ids))
            .group_by(IngredientExit.ingredient_id)
        ).all()
    )

    return {
        ingredient_id: float(inbound.get(ingredient_id, 0.0))
        - float(outbound.get(ingredient_id, 0.0))
        for ingredient_id in ids
    }


def current_stock(session: Session, ingredient_id: int) -> float:
    return stock_by_ingredient_ids(session, [ingredient_id]).get(ingredient_id, 0.0)


def insufficient_stock_message(name: str, available: float, requested: float) -> str:
    return (
        f"Insufficient stock for ingredient '{name}'. "
        f"Available: {available}, requested: {requested}."
    )
