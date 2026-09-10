"""Brasaland inventory HTTP routes under /inventory."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.auth.deps import get_current_user
from app.inventory.db import get_inventory_session
from app.inventory.models import Ingredient, IngredientEntry, IngredientExit
from app.inventory.schemas import (
    InboundCreate,
    InboundRead,
    IngredientCreate,
    IngredientPublic,
    IngredientRead,
    OrderListItem,
    OutboundCreate,
    OutboundRead,
)
from app.inventory.stock import (
    current_stock,
    insufficient_stock_message,
    stock_by_ingredient_ids,
)

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(get_current_user)],
)


def _tiny_user_ref(current_user: dict) -> str:
    return str(current_user["id"])


def _ingredient_read(session: Session, ingredient: Ingredient) -> IngredientRead:
    stock = current_stock(session, ingredient.id)
    public = IngredientPublic.model_validate(ingredient)
    return IngredientRead(**public.model_dump(), current_stock=stock)


@router.get("/products", response_model=list[IngredientRead])
def list_products(
    country: str | None = Query(default=None),
    session: Session = Depends(get_inventory_session),
) -> list[IngredientRead]:
    statement = select(Ingredient)
    if country:
        statement = statement.where(Ingredient.country == country.strip().upper())
    statement = statement.order_by(Ingredient.sku)
    rows = list(session.exec(statement).all())
    stocks = stock_by_ingredient_ids(session, [row.id for row in rows if row.id])
    return [
        IngredientRead(
            **IngredientPublic.model_validate(row).model_dump(),
            current_stock=stocks.get(row.id, 0.0),
        )
        for row in rows
    ]


@router.post("/products", response_model=IngredientRead, status_code=201)
def create_product(
    payload: IngredientCreate,
    session: Session = Depends(get_inventory_session),
) -> IngredientRead:
    taken = session.exec(
        select(Ingredient).where(Ingredient.sku == payload.sku)
    ).first()
    if taken is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="sku already registered",
        )
    ingredient = Ingredient(**payload.model_dump())
    session.add(ingredient)
    session.commit()
    session.refresh(ingredient)
    return _ingredient_read(session, ingredient)


@router.get("/products/{ingredient_id}", response_model=IngredientRead)
def get_product(
    ingredient_id: int,
    session: Session = Depends(get_inventory_session),
) -> IngredientRead:
    ingredient = session.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return _ingredient_read(session, ingredient)


@router.post("/orders/inbound", response_model=InboundRead, status_code=201)
def create_inbound(
    payload: InboundCreate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_inventory_session),
) -> InboundRead:
    ingredient = session.get(Ingredient, payload.ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    entry = IngredientEntry(
        **payload.model_dump(),
        user_uuid=_tiny_user_ref(current_user),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return InboundRead(
        **entry.model_dump(),
        ingredient=IngredientPublic.model_validate(ingredient),
    )


@router.post("/orders/outbound", response_model=OutboundRead, status_code=201)
def create_outbound(
    payload: OutboundCreate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_inventory_session),
) -> OutboundRead:
    ingredient = session.get(Ingredient, payload.ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    available = current_stock(session, ingredient.id)
    if payload.quantity > available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=insufficient_stock_message(
                ingredient.name, available, payload.quantity
            ),
        )
    exit_row = IngredientExit(
        **payload.model_dump(),
        user_uuid=_tiny_user_ref(current_user),
    )
    session.add(exit_row)
    session.commit()
    session.refresh(exit_row)
    return OutboundRead(
        **exit_row.model_dump(),
        ingredient=IngredientPublic.model_validate(ingredient),
    )


@router.get("/orders", response_model=list[OrderListItem])
def list_orders(
    session: Session = Depends(get_inventory_session),
) -> list[OrderListItem]:
    entries = list(session.exec(select(IngredientEntry)).all())
    exits = list(session.exec(select(IngredientExit)).all())
    ingredient_ids = {row.ingredient_id for row in entries} | {
        row.ingredient_id for row in exits
    }
    ingredients = {}
    if ingredient_ids:
        loaded = session.exec(
            select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
        ).all()
        ingredients = {row.id: row for row in loaded}

    items: list[OrderListItem] = []
    for entry in entries:
        ingredient = ingredients.get(entry.ingredient_id)
        if ingredient is None:
            continue
        items.append(
            OrderListItem(
                type="entry",
                id=entry.id,
                ingredient_id=entry.ingredient_id,
                quantity=entry.quantity,
                location_id=entry.location_id,
                created_at=entry.created_at,
                user_uuid=entry.user_uuid,
                ingredient=IngredientPublic.model_validate(ingredient),
                supplier_name=entry.supplier_name,
            )
        )
    for exit_row in exits:
        ingredient = ingredients.get(exit_row.ingredient_id)
        if ingredient is None:
            continue
        items.append(
            OrderListItem(
                type="exit",
                id=exit_row.id,
                ingredient_id=exit_row.ingredient_id,
                quantity=exit_row.quantity,
                location_id=exit_row.location_id,
                created_at=exit_row.created_at,
                user_uuid=exit_row.user_uuid,
                ingredient=IngredientPublic.model_validate(ingredient),
                reason=exit_row.reason,
            )
        )
    items.sort(key=lambda row: row.created_at, reverse=True)
    return items
