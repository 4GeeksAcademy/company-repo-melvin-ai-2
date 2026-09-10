"""Pydantic request/response schemas for /inventory. Never return ORM rows."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

INGREDIENT_UNITS = ("kg", "litre", "unit")
INGREDIENT_CATEGORIES = (
    "meat",
    "produce",
    "sauce",
    "beverage",
    "packaging",
    "cleaning",
)
INGREDIENT_COUNTRIES = ("CO", "US")
EXIT_REASONS = ("consumption", "waste")


class IngredientCreate(BaseModel):
    name: str = Field(min_length=1)
    sku: str = Field(min_length=1)
    unit: str
    category: str
    country: str

    @field_validator("name", "sku")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value is required")
        return cleaned

    @field_validator("unit")
    @classmethod
    def unit_allowed(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in INGREDIENT_UNITS:
            raise ValueError(f"unit must be one of {INGREDIENT_UNITS}")
        return cleaned

    @field_validator("category")
    @classmethod
    def category_allowed(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in INGREDIENT_CATEGORIES:
            raise ValueError(f"category must be one of {INGREDIENT_CATEGORIES}")
        return cleaned

    @field_validator("country")
    @classmethod
    def country_allowed(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if cleaned not in INGREDIENT_COUNTRIES:
            raise ValueError('country must be "CO" or "US"')
        return cleaned


class IngredientPublic(BaseModel):
    """Ingredient fields shared on order rows (no stock)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sku: str
    unit: str
    category: str
    country: str


class IngredientRead(IngredientPublic):
    current_stock: float


class InboundCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    supplier_name: str = Field(min_length=1)
    location_id: int = Field(ge=1, le=14)

    @field_validator("supplier_name")
    @classmethod
    def supplier_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("supplier_name is required")
        return cleaned


class OutboundCreate(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)
    reason: str
    location_id: int = Field(ge=1, le=14)

    @field_validator("reason")
    @classmethod
    def reason_allowed(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned not in EXIT_REASONS:
            raise ValueError('reason must be "consumption" or "waste"')
        return cleaned


class InboundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    supplier_name: str
    location_id: int
    created_at: datetime
    user_uuid: str
    ingredient: IngredientPublic


class OutboundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ingredient_id: int
    quantity: float
    reason: str
    location_id: int
    created_at: datetime
    user_uuid: str
    ingredient: IngredientPublic


class OrderListItem(BaseModel):
    type: Literal["entry", "exit"]
    id: int
    ingredient_id: int
    quantity: float
    location_id: int
    created_at: datetime
    user_uuid: str
    ingredient: IngredientPublic
    supplier_name: Optional[str] = None
    reason: Optional[str] = None
