"""Write-only bulk insert for telemetry_events. One statement per batch."""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Column, DateTime, MetaData, Table, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.inventory.db import database_url, get_engine

SERVICE_NAME = "backoffice"
_SCHEMA_PATH = (
    Path(__file__).resolve().parents[4] / "docs" / "telemetry" / "event-schemas.json"
)
_DDL_PATH = Path(__file__).with_name("schema.sql")
_ready = False

metadata = MetaData()
telemetry_events = Table(
    "telemetry_events",
    metadata,
    Column("event_id", Text, primary_key=True),
    Column("timestamp", DateTime(timezone=True), nullable=False),
    Column("session_id", Text, nullable=False),
    Column("user_id", Text),
    Column("event_type", Text, nullable=False),
    Column("service", Text, nullable=False),
    Column("request_id", Text, nullable=False),
    Column("tags", JSONB, nullable=False),
)


def _walk_keys(schema: dict, node: dict) -> set[str]:
    if "$ref" in node:
        name = node["$ref"].rsplit("/", 1)[-1]
        return _walk_keys(schema, schema["definitions"][name])
    keys: set[str] = set()
    for item in node.get("allOf", []):
        keys |= _walk_keys(schema, item)
    keys |= set(node.get("properties") or {})
    return keys


@lru_cache(maxsize=1)
def property_allowlists() -> dict[str, frozenset[str]]:
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    allowlists: dict[str, frozenset[str]] = {}
    for event_type, definition in schema["definitions"].items():
        inner = None
        for item in definition.get("allOf", []):
            declared = item.get("properties") or {}
            if "properties" in declared:
                inner = declared["properties"]
        if inner is not None:
            allowlists[event_type] = frozenset(_walk_keys(schema, inner))
    return allowlists


def tags_for(event_type: str, properties: dict) -> dict:
    """Keep only keys the Phase 1 plan allows for this event_type."""
    allowed = property_allowlists().get(event_type, frozenset())
    return {key: value for key, value in properties.items() if key in allowed}


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sql_statements(script: str) -> list[str]:
    """Split schema.sql on semicolons that are outside the trigger function body."""
    statements: list[str] = []
    current: list[str] = []
    in_body = False
    for line in script.splitlines(keepends=True):
        if line.strip().startswith("--"):
            continue
        current.append(line)
        if "$$" in line:
            in_body = not in_body
        if not in_body and line.rstrip().endswith(";"):
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
    return statements


def ensure_telemetry_table() -> None:
    global _ready
    if _ready or not database_url():
        return
    engine = get_engine()
    with engine.begin() as connection:
        for statement in _sql_statements(_DDL_PATH.read_text(encoding="utf-8")):
            connection.exec_driver_sql(statement)
    _ready = True


def insert_batch(rows: list[dict]) -> int:
    """Insert every row in one statement. Duplicate event_id values are skipped."""
    if not rows:
        return 0
    ensure_telemetry_table()
    statement = (
        pg_insert(telemetry_events)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["event_id"])
        .returning(telemetry_events.c.event_id)
    )
    engine = get_engine()
    with engine.begin() as connection:
        inserted = connection.execute(statement).fetchall()
    return len(inserted)
