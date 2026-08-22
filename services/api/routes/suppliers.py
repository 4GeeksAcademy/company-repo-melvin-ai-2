"""Supplier directory FastAPI routes."""

from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

import database
from models import (
    RateUpdate,
    StatusUpdate,
    SupplierCreate,
    SupplierResponse,
    utc_now,
)
from seed import run_seed

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


def _as_response(row: dict) -> SupplierResponse:
    return SupplierResponse.model_validate(row)


@router.post("", response_model=SupplierResponse, status_code=201)
@router.post("/", response_model=SupplierResponse, status_code=201, include_in_schema=False)
def create_supplier(payload: SupplierCreate) -> SupplierResponse:
    data = payload.model_dump(mode="json")
    data["updated_at"] = None
    created = database.insert_supplier(data)
    return _as_response(created)


@router.get("", response_model=List[SupplierResponse])
@router.get("/", response_model=List[SupplierResponse], include_in_schema=False)
def list_suppliers(
    country: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
) -> List[SupplierResponse]:
    rows = database.list_suppliers(country=country, category=category)
    return [_as_response(row) for row in rows]


@router.post("/admin/seed", include_in_schema=False)
def seed_via_api() -> Dict[str, int]:
    """Optional helper for demos; preferred path is `uv run seed`."""
    inserted = run_seed()
    return {"inserted": inserted}


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int) -> SupplierResponse:
    row = database.get_supplier(supplier_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _as_response(row)


@router.patch("/{supplier_id}/rate", response_model=SupplierResponse)
def update_rate(supplier_id: int, payload: RateUpdate) -> SupplierResponse:
    updated = database.update_supplier(
        supplier_id,
        {
            "rate_per_unit": payload.rate_per_unit,
            "updated_at": utc_now().isoformat(),
        },
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _as_response(updated)


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
def update_status(supplier_id: int, payload: StatusUpdate) -> SupplierResponse:
    updated = database.update_supplier(
        supplier_id,
        {"status": payload.status.value},
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _as_response(updated)


@router.delete("/{supplier_id}", status_code=204)
def delete_supplier(supplier_id: int) -> None:
    if not database.delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
