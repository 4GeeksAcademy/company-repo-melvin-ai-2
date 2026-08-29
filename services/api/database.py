"""TinyDB persistence for Brasaland suppliers."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from tinydb import Query, TinyDB

from app.errors import PersistenceError

DB_PATH = Path(__file__).resolve().parent / "data" / "suppliers.json"


def get_db() -> TinyDB:
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return TinyDB(DB_PATH)
    except OSError as exc:
        raise PersistenceError("Could not open the supplier directory.") from exc


def doc_to_supplier(doc_id: int, doc: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(doc)
    payload["id"] = doc_id
    return payload


def list_suppliers(
    *,
    country: Optional[str] = None,
    category: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_db()
    table = db.table("suppliers")
    rows: List[Dict[str, Any]] = []
    for doc in table.all():
        item = doc_to_supplier(doc.doc_id, dict(doc))
        if country and item.get("country") != country:
            continue
        if category:
            cats = item.get("categories") or []
            if category not in cats:
                continue
        rows.append(item)
    rows.sort(key=lambda row: row.get("name") or "")
    return rows


def get_supplier(supplier_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    table = db.table("suppliers")
    doc = table.get(doc_id=supplier_id)
    if doc is None:
        return None
    return doc_to_supplier(supplier_id, dict(doc))


def insert_supplier(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        db = get_db()
        table = db.table("suppliers")
        doc_id = table.insert(data)
        return doc_to_supplier(doc_id, data)
    except PersistenceError:
        raise
    except OSError as exc:
        raise PersistenceError("Could not save the supplier.") from exc


def update_supplier(
    supplier_id: int, patch: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    try:
        db = get_db()
        table = db.table("suppliers")
        existing = table.get(doc_id=supplier_id)
        if existing is None:
            return None
        merged = dict(existing)
        merged.update(patch)
        table.update(merged, doc_ids=[supplier_id])
        return doc_to_supplier(supplier_id, merged)
    except PersistenceError:
        raise
    except OSError as exc:
        raise PersistenceError("Could not update the supplier.") from exc


def delete_supplier(supplier_id: int) -> bool:
    db = get_db()
    table = db.table("suppliers")
    removed = table.remove(doc_ids=[supplier_id])
    return bool(removed)


def find_by_name(name: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    table = db.table("suppliers")
    Supplier = Query()
    doc = table.get(Supplier.name == name)
    if doc is None:
        return None
    return doc_to_supplier(doc.doc_id, dict(doc))


def count_suppliers() -> int:
    db = get_db()
    return len(db.table("suppliers"))
