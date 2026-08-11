"""Idempotent seeder for CONTEXT suppliers."""

from __future__ import annotations

from app.suppliers.db import count_suppliers, find_by_name, insert_supplier
from app.suppliers.models import SupplierCreate
from app.suppliers.seed_data import SUPPLIERS_SEED


def run_seed() -> int:
    """Insert missing CONTEXT suppliers. Returns number of new records inserted."""
    inserted = 0
    for raw in SUPPLIERS_SEED:
        validated = SupplierCreate.model_validate(raw)
        if find_by_name(validated.name) is not None:
            continue
        payload = validated.model_dump(mode="json")
        payload["updated_at"] = None
        insert_supplier(payload)
        inserted += 1
    return inserted


def seed_command() -> None:
    before = count_suppliers()
    inserted = run_seed()
    after = count_suppliers()
    print(f"Seed complete: inserted {inserted} supplier(s).")
    print(f"TinyDB now has {after} supplier(s) (was {before} before this run).")
