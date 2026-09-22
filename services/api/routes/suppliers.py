"""Supplier directory FastAPI routes."""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.deps import get_current_user
from app.cache import (
    CATALOG_TTL_SECONDS,
    SUPPLIERS_PREFIX,
    catalog_cache,
    invalidate_supplier_catalog,
)
import database
from models import (
    RateUpdate,
    StatusUpdate,
    SeedResponse,
    SupplierCreate,
    SupplierResponse,
    utc_now,
)
from seed import run_seed

router = APIRouter(
    prefix="/suppliers",
    tags=["suppliers"],
    dependencies=[Depends(get_current_user)],
)


def _as_response(row: dict) -> SupplierResponse:
    return SupplierResponse.model_validate(row)


@router.post("", response_model=SupplierResponse, status_code=201)
@router.post("/", response_model=SupplierResponse, status_code=201, include_in_schema=False)
def create_supplier(payload: SupplierCreate) -> SupplierResponse:
    data = payload.model_dump(mode="json")
    data["updated_at"] = None
    created = database.insert_supplier(data)
    invalidate_supplier_catalog()
    return _as_response(created)


@router.get("", response_model=List[SupplierResponse])
@router.get("/", response_model=List[SupplierResponse], include_in_schema=False)
def list_suppliers(
    country: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
) -> List[SupplierResponse]:
    # Directory rows are the same for every signed-in operator. Key is the
    # filter pair only — never the Bearer user.
    cache_key = f"{SUPPLIERS_PREFIX}{country or '*'}|{category or '*'}"
    cached = catalog_cache.get(cache_key)
    if isinstance(cached, list):
        return [SupplierResponse.model_validate(row) for row in cached]
    rows = database.list_suppliers(country=country, category=category)
    payload = [_as_response(row) for row in rows]
    catalog_cache.set(
        cache_key,
        [row.model_dump(mode="json") for row in payload],
        CATALOG_TTL_SECONDS,
    )
    return payload


@router.post("/admin/seed", response_model=SeedResponse, include_in_schema=False)
def seed_via_api() -> SeedResponse:
    """Optional helper for demos; preferred path is `uv run seed`."""
    inserted = run_seed()
    invalidate_supplier_catalog()
    return SeedResponse(inserted=inserted)


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
    invalidate_supplier_catalog()
    return _as_response(updated)


@router.patch("/{supplier_id}/status", response_model=SupplierResponse)
def update_status(supplier_id: int, payload: StatusUpdate) -> SupplierResponse:
    updated = database.update_supplier(
        supplier_id,
        {"status": payload.status.value},
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    invalidate_supplier_catalog()
    return _as_response(updated)


@router.delete("/{supplier_id}", status_code=204, response_model=None)
def delete_supplier(supplier_id: int) -> None:
    if not database.delete_supplier(supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")
    invalidate_supplier_catalog()
