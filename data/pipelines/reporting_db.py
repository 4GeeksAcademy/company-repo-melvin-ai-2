"""Postgres reads and writes for the weekly location report.

The connection is ``DATABASE_URL`` via ``app.inventory.db.get_engine``. That
URI is the Supabase transaction pooler. The Prefect block ``brasaland-supabase``
names the same secret; the password is not stored in this file.
"""

from __future__ import annotations

import json
import sys
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY

API_ROOT = Path(__file__).resolve().parents[2] / "services" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.inventory.db import get_engine  # noqa: E402

EVENT_TYPES = (
    "inbound_order_created",
    "outbound_order_created",
    "stock_waste_registered",
    "stock_threshold_triggered",
    "ingredient_price_variance_detected",
)

# A crashed run older than this is marked Failed so the week can start again.
STALE_RUN_AFTER = timedelta(minutes=30)

_SCHEMA = "CREATE SCHEMA IF NOT EXISTS reporting"

_PERFORMANCE = """
CREATE TABLE IF NOT EXISTS reporting.weekly_location_performance (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  location_id text NOT NULL,
  country text NOT NULL,
  week_start date NOT NULL,
  total_purchase_cost numeric NOT NULL DEFAULT 0,
  total_waste_cost numeric NOT NULL DEFAULT 0,
  waste_ratio numeric NOT NULL DEFAULT 0,
  stockout_events_count integer NOT NULL DEFAULT 0,
  price_alert_events_count integer NOT NULL DEFAULT 0,
  currency text NOT NULL,
  computed_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (location_id, week_start)
)
"""

_RUNS = """
CREATE TABLE IF NOT EXISTS reporting.weekly_performance_run (
  run_id uuid PRIMARY KEY,
  week_start date NOT NULL,
  status text NOT NULL,
  started_at timestamptz NOT NULL,
  ended_at timestamptz,
  records_read integer NOT NULL DEFAULT 0,
  records_loaded integer NOT NULL DEFAULT 0,
  events_skipped_missing_cost integer NOT NULL DEFAULT 0,
  error_message text NOT NULL DEFAULT ''
)
"""

UPSERT_SQL = """
INSERT INTO reporting.weekly_location_performance (
  location_id, country, week_start,
  total_purchase_cost, total_waste_cost, waste_ratio,
  stockout_events_count, price_alert_events_count,
  currency, computed_at
) VALUES (
  :location_id, :country, :week_start,
  :total_purchase_cost, :total_waste_cost, :waste_ratio,
  :stockout_events_count, :price_alert_events_count,
  :currency, :computed_at
)
ON CONFLICT (location_id, week_start) DO UPDATE SET
  country = EXCLUDED.country,
  total_purchase_cost = EXCLUDED.total_purchase_cost,
  total_waste_cost = EXCLUDED.total_waste_cost,
  waste_ratio = EXCLUDED.waste_ratio,
  stockout_events_count = EXCLUDED.stockout_events_count,
  price_alert_events_count = EXCLUDED.price_alert_events_count,
  currency = EXCLUDED.currency,
  computed_at = EXCLUDED.computed_at
"""

_EXTRACT = text(
    """
    SELECT event_id, timestamp, event_type, tags
    FROM telemetry_events
    WHERE timestamp >= :start
      AND timestamp < :end
      AND event_type = ANY(:event_types)
    ORDER BY timestamp, event_id
    """
).bindparams(bindparam("event_types", type_=ARRAY(String)))


def ensure_reporting_tables() -> None:
    with get_engine().begin() as connection:
        connection.execute(text(_SCHEMA))
        connection.execute(text(_PERFORMANCE))
        connection.execute(text(_RUNS))


def fetch_week_events(week_start: date) -> list[dict]:
    start, end = _week_bounds(week_start)
    with get_engine().connect() as connection:
        rows = connection.execute(
            _EXTRACT,
            {"start": start, "end": end, "event_types": list(EVENT_TYPES)},
        ).mappings()
        return [_event_dict(row) for row in rows]


def begin_run(week_start: date) -> str:
    ensure_reporting_tables()
    run_id = str(uuid.uuid4())
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO reporting.weekly_performance_run (
                  run_id, week_start, status, started_at, error_message
                ) VALUES (
                  :run_id, :week_start, 'Running', :started_at, ''
                )
                """
            ),
            {
                "run_id": run_id,
                "week_start": week_start,
                "started_at": _now(),
            },
        )
    return run_id


def fail_stale_runs(week_start: date) -> None:
    ensure_reporting_tables()
    cutoff = _now() - STALE_RUN_AFTER
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                UPDATE reporting.weekly_performance_run
                SET status = 'Failed',
                    ended_at = :ended_at,
                    error_message = :error_message,
                    records_loaded = 0
                WHERE week_start = :week_start
                  AND status = 'Running'
                  AND started_at < :cutoff
                """
            ),
            {
                "ended_at": _now(),
                "error_message": (
                    "Run exceeded 30 minutes and was marked Failed "
                    "so this week can start again."
                ),
                "week_start": week_start,
                "cutoff": cutoff,
            },
        )


def insert_failed_attempt(week_start: date, error_message: str) -> str:
    ensure_reporting_tables()
    run_id = str(uuid.uuid4())
    now = _now()
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO reporting.weekly_performance_run (
                  run_id, week_start, status, started_at, ended_at,
                  records_read, records_loaded, events_skipped_missing_cost,
                  error_message
                ) VALUES (
                  :run_id, :week_start, 'Failed', :started_at, :ended_at,
                  0, 0, 0, :error_message
                )
                """
            ),
            {
                "run_id": run_id,
                "week_start": week_start,
                "started_at": now,
                "ended_at": now,
                "error_message": error_message,
            },
        )
    return run_id


def fail_run(
    run_id: str,
    error_message: str,
    records_read: int = 0,
    events_skipped_missing_cost: int = 0,
) -> None:
    with get_engine().begin() as connection:
        connection.execute(
            text(
                """
                UPDATE reporting.weekly_performance_run
                SET status = 'Failed',
                    ended_at = :ended_at,
                    records_read = :records_read,
                    records_loaded = 0,
                    events_skipped_missing_cost = :events_skipped_missing_cost,
                    error_message = :error_message
                WHERE run_id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "ended_at": _now(),
                "records_read": records_read,
                "events_skipped_missing_cost": events_skipped_missing_cost,
                "error_message": error_message[:500],
            },
        )


def load_week(run_id: str, week_start: date, transformed: dict) -> dict:
    """Upsert every location and mark the run Completed in one transaction."""
    rows = transformed.get("rows") or []
    records_read = int(transformed.get("records_read") or 0)
    skipped = int(transformed.get("events_skipped_missing_cost") or 0)
    computed_at = _now()
    with get_engine().begin() as connection:
        for row in rows:
            connection.execute(
                text(UPSERT_SQL),
                {
                    "location_id": row["location_id"],
                    "country": row["country"],
                    "week_start": week_start,
                    "total_purchase_cost": Decimal(row["total_purchase_cost"]),
                    "total_waste_cost": Decimal(row["total_waste_cost"]),
                    "waste_ratio": Decimal(row["waste_ratio"]),
                    "stockout_events_count": int(row["stockout_events_count"]),
                    "price_alert_events_count": int(row["price_alert_events_count"]),
                    "currency": row["currency"],
                    "computed_at": computed_at,
                },
            )
        connection.execute(
            text(
                """
                UPDATE reporting.weekly_performance_run
                SET status = 'Completed',
                    ended_at = :ended_at,
                    records_read = :records_read,
                    records_loaded = :records_loaded,
                    events_skipped_missing_cost = :events_skipped_missing_cost,
                    error_message = ''
                WHERE run_id = :run_id
                """
            ),
            {
                "run_id": run_id,
                "ended_at": computed_at,
                "records_read": records_read,
                "records_loaded": len(rows),
                "events_skipped_missing_cost": skipped,
            },
        )
        stored = (
            connection.execute(
                text(
                    """
                    SELECT run_id, week_start, status, started_at, ended_at,
                           records_read, records_loaded,
                           events_skipped_missing_cost, error_message
                    FROM reporting.weekly_performance_run
                    WHERE run_id = :run_id
                    """
                ),
                {"run_id": run_id},
            )
            .mappings()
            .one()
        )
    return _run_payload(
        run_id=str(stored["run_id"]),
        week_start=stored["week_start"],
        status=stored["status"],
        started_at=stored["started_at"],
        ended_at=stored["ended_at"],
        records_read=stored["records_read"],
        records_loaded=stored["records_loaded"],
        events_skipped_missing_cost=stored["events_skipped_missing_cost"],
        error_message=stored["error_message"] or "",
    )


def latest_weekly_performance_run() -> dict | None:
    ensure_reporting_tables()
    with get_engine().connect() as connection:
        row = (
            connection.execute(
                text(
                    """
                    SELECT run_id, week_start, status, started_at, ended_at,
                           records_read, records_loaded,
                           events_skipped_missing_cost, error_message
                    FROM reporting.weekly_performance_run
                    ORDER BY started_at DESC
                    LIMIT 1
                    """
                )
            )
            .mappings()
            .first()
        )
    if row is None:
        return None
    return _run_payload(
        run_id=str(row["run_id"]),
        week_start=row["week_start"],
        status=row["status"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        records_read=row["records_read"],
        records_loaded=row["records_loaded"],
        events_skipped_missing_cost=row["events_skipped_missing_cost"],
        error_message=row["error_message"] or "",
    )


def read_weekly_location_performance(week_start: date | None = None) -> dict:
    ensure_reporting_tables()
    with get_engine().connect() as connection:
        if week_start is None:
            found = connection.execute(
                text(
                    """
                    SELECT max(week_start) AS week_start
                    FROM reporting.weekly_location_performance
                    """
                )
            ).scalar()
            if found is None:
                return {"week_start": None, "locations": []}
            week_start = found
        rows = (
            connection.execute(
                text(
                    """
                    SELECT location_id, country, total_purchase_cost,
                           total_waste_cost, waste_ratio,
                           stockout_events_count, price_alert_events_count,
                           currency
                    FROM reporting.weekly_location_performance
                    WHERE week_start = :week_start
                    ORDER BY location_id
                    """
                ),
                {"week_start": week_start},
            )
            .mappings()
            .all()
        )
    return {
        "week_start": week_start.isoformat(),
        "locations": [_location_payload(row) for row in rows],
    }


@contextmanager
def hold_week_lock(week_start: date):
    """Hold the week lock until the flow returns.

    ``pg_try_advisory_lock`` is session-scoped. Supabase port 6543 is a
    transaction pooler, so a session lock is dropped when that transaction
    ends. ``pg_try_advisory_xact_lock`` stays until this transaction commits,
    which is after the flow finishes. The key is the week as ``YYYYMMDD``.
    """
    key = int(week_start.strftime("%Y%m%d"))
    connection = get_engine().connect()
    transaction = connection.begin()
    try:
        locked = connection.execute(
            text("SELECT pg_try_advisory_xact_lock(:key)"),
            {"key": key},
        ).scalar()
        yield bool(locked)
        transaction.commit()
    except Exception:
        transaction.rollback()
        raise
    finally:
        connection.close()


def _week_bounds(week_start: date) -> tuple[datetime, datetime]:
    start = datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc)
    return start, start + timedelta(days=7)


def _event_dict(row) -> dict:
    tags = row["tags"]
    if isinstance(tags, str):
        try:
            tags = json.loads(tags)
        except json.JSONDecodeError:
            tags = {}
    if not isinstance(tags, dict):
        tags = {}
    return {
        "event_id": row["event_id"],
        "timestamp": row["timestamp"],
        "event_type": row["event_type"],
        "tags": tags,
    }


def _location_payload(row) -> dict:
    return {
        "location_id": row["location_id"],
        "country": row["country"],
        "total_purchase_cost": float(row["total_purchase_cost"]),
        "total_waste_cost": float(row["total_waste_cost"]),
        "waste_ratio": float(row["waste_ratio"]),
        "stockout_events_count": int(row["stockout_events_count"]),
        "price_alert_events_count": int(row["price_alert_events_count"]),
        "currency": row["currency"],
    }


def _run_payload(
    *,
    run_id: str,
    week_start: date,
    status: str,
    started_at: datetime | None,
    ended_at: datetime | None,
    records_read: int,
    records_loaded: int,
    events_skipped_missing_cost: int,
    error_message: str,
) -> dict:
    return {
        "run_id": str(run_id),
        "week_start": week_start.isoformat() if isinstance(week_start, date) else week_start,
        "status": status,
        "started_at": _iso(started_at),
        "ended_at": _iso(ended_at),
        "records_read": int(records_read or 0),
        "records_loaded": int(records_loaded or 0),
        "records_processed": int(records_read or 0),
        "events_skipped_missing_cost": int(events_skipped_missing_cost or 0),
        "error_message": error_message or "",
    }


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _now() -> datetime:
    return datetime.now(timezone.utc)
