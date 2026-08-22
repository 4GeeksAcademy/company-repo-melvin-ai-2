"""Brasaland supplier Pydantic models (CONTEXT field names)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_CATEGORIES = [
    "carne",
    "verduras_y_hortalizas",
    "salsas_y_condimentos",
    "bebidas",
    "packaging",
    "productos_limpieza",
    "lacteos",
    "carbon_y_combustible",
]

VALID_COUNTRIES = ("Colombia", "USA")
VALID_CURRENCIES = ("COP", "USD")


class SupplierStatus(str, Enum):
    active = "active"
    suspended = "suspended"


Country = Literal["Colombia", "USA"]
Currency = Literal["COP", "USD"]


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1)
    country: Country
    categories: List[str] = Field(min_length=1)
    rate_per_unit: float = Field(gt=0)
    currency: Currency
    status: SupplierStatus = SupplierStatus.active
    contact_email: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name is required")
        return cleaned

    @field_validator("categories")
    @classmethod
    def categories_must_be_valid(cls, value: List[str]) -> List[str]:
        if not value:
            raise ValueError("categories must include at least one item")
        cleaned: List[str] = []
        for item in value:
            cat = item.strip()
            if cat not in VALID_CATEGORIES:
                raise ValueError(
                    f"invalid category '{item}'; allowed: {VALID_CATEGORIES}"
                )
            if cat not in cleaned:
                cleaned.append(cat)
        if not cleaned:
            raise ValueError("categories must include at least one valid item")
        return cleaned

    @model_validator(mode="after")
    def currency_matches_country(self) -> SupplierCreate:
        if self.country == "Colombia" and self.currency != "COP":
            raise ValueError('Colombia suppliers must use currency "COP"')
        if self.country == "USA" and self.currency != "USD":
            raise ValueError('USA suppliers must use currency "USD"')
        return self


class SupplierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country: Country
    categories: List[str]
    rate_per_unit: float
    currency: Currency
    status: SupplierStatus
    updated_at: Optional[datetime] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None


class RateUpdate(BaseModel):
    rate_per_unit: float = Field(gt=0)


class StatusUpdate(BaseModel):
    status: SupplierStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
