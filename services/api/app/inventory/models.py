"""SQLModel tables for Brasaland ingredients in Supabase. No stock column."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredients"
    __table_args__ = (UniqueConstraint("sku", name="uq_ingredients_sku"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True)
    unit: str
    category: str
    country: str


class IngredientEntry(SQLModel, table=True):
    __tablename__ = "ingredient_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredients.id", index=True)
    quantity: float
    supplier_name: str
    location_id: int
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    user_uuid: str


class IngredientExit(SQLModel, table=True):
    __tablename__ = "ingredient_exits"

    id: Optional[int] = Field(default=None, primary_key=True)
    ingredient_id: int = Field(foreign_key="ingredients.id", index=True)
    quantity: float
    reason: str
    location_id: int
    created_at: datetime = Field(
        default_factory=_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    user_uuid: str
