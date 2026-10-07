"""Weekly Location Cost & Waste Report.

Schedule: Monday 11:00 UTC (06:00 Colombia, 07:00 Florida). The run recomputes
the ISO week that just ended.

From the repo root, with the API environment:

    python data/pipelines/pipeline.py

An optional ``YYYY-MM-DD`` argument recomputes that week. The connection is
``DATABASE_URL`` (Prefect block ``brasaland-supabase``). This file does not
print or store the password.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Prefect 3 starts a local API the first time a flow runs. The default 20s
# wait is tight on a cold start, so give that process a minute.
os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "60")

from prefect import flow, task  # noqa: E402
from prefect.states import State  # noqa: E402

from data.pipelines import reporting_db  # noqa: E402
from data.process.weekly_location_performance import (  # noqa: E402
    aggregate_location_week,
    monday_of,
    previous_completed_week,
)

logger = logging.getLogger("brasaland.pipeline")
EVAL_DIR = ROOT / "data" / "eval"

# Three tries cover a brief Supabase pooler blip. Five seconds gives the
# pooler time to hand back a live connection before the next attempt.
_DB_RETRIES = 3
_DB_RETRY_DELAY_SECONDS = 5


def _transform_cache_key(_context, parameters: dict) -> str:
    """Cache key is the UTC week plus the event ids in that extract.

    A successful transform is reused for one hour. A new event id changes the
    key, so a late event is not served from the previous result.
    """
    week = parameters["week_start"]
    week_text = week.isoformat() if isinstance(week, date) else str(week)
    events = parameters.get("events") or []
    identity = ",".join(sorted(str(event.get("event_id") or "") for event in events))
    digest = hashlib.sha256(identity.encode()).hexdigest()
    return f"{week_text}:{digest}"


@task(
    name="extract_weekly_events",
    retries=_DB_RETRIES,
    retry_delay_seconds=_DB_RETRY_DELAY_SECONDS,
)
def extract_weekly_events(week_start: date) -> list[dict]:
    """Read one half-open UTC week from ``telemetry_events``."""
    return reporting_db.fetch_week_events(week_start)


@task(
    name="transform_location_week",
    cache_key_fn=_transform_cache_key,
    cache_expiration=timedelta(hours=1),
)
def transform_location_week(week_start: date, events: list[dict]) -> dict:
    """Aggregate to one row per location. Cached for one hour."""
    return aggregate_location_week(week_start, events)


@task(name="write_eval_snapshot")
def write_eval_snapshot(week_start: date, transformed: dict) -> str:
    """Optional context file. Outbound volume is not a KPI.

    A failure here must not stop extract, transform, or load. The flow calls
    this task with ``return_state=True``.
    """
    if os.environ.get("BRASALAND_EVAL_SNAPSHOT_FAIL") == "1":
        raise RuntimeError("eval snapshot failed")
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    path = EVAL_DIR / f"weekly_location_performance_{week_start.isoformat()}.json"
    payload = {
        "week_start": week_start.isoformat(),
        "outbound_events_count": transformed.get("outbound_events_count", 0),
        "locations": len(transformed.get("rows") or []),
        "events_skipped_missing_cost": transformed.get("events_skipped_missing_cost", 0),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


@task(
    name="load_weekly_location_performance",
    retries=_DB_RETRIES,
    retry_delay_seconds=_DB_RETRY_DELAY_SECONDS,
)
def load_weekly_location_performance(
    run_id: str, week_start: date, transformed: dict
) -> dict:
    """Upsert the week and mark the run Completed in one transaction."""
    return reporting_db.load_week(run_id, week_start, transformed)


@flow(name="weekly_location_performance")
def weekly_location_performance(week_start: date, run_id: str) -> dict:
    """Extract, transform, and load one location week.

    ``write_eval_snapshot`` is optional. Its failure is recorded and the load
    still runs.
    """
    events = extract_weekly_events(week_start)
    transformed = transform_location_week(week_start, events)
    snapshot: State = write_eval_snapshot(week_start, transformed, return_state=True)
    if snapshot.is_failed():
        logger.warning("Eval snapshot was skipped: %s", snapshot.message)
    return load_weekly_location_performance(run_id, week_start, transformed)


def request_weekly_location_performance_run(week_start: date | None = None) -> dict:
    """Take the week lock, then start ``weekly_location_performance``.

    A second caller for the same week does not start the flow. It writes a
    Failed run row and returns that ``run_id``.
    """
    week = monday_of(week_start) if week_start else previous_completed_week()
    reporting_db.ensure_reporting_tables()
    with reporting_db.hold_week_lock(week) as acquired:
        if not acquired:
            message = "This week is already running."
            run_id = reporting_db.insert_failed_attempt(week, message)
            return {
                "run_id": run_id,
                "week_start": week.isoformat(),
                "status": "Failed",
                "started_at": None,
                "ended_at": None,
                "records_read": 0,
                "records_loaded": 0,
                "records_processed": 0,
                "events_skipped_missing_cost": 0,
                "error_message": message,
            }
        reporting_db.fail_stale_runs(week)
        run_id = reporting_db.begin_run(week)
        try:
            return weekly_location_performance(week, run_id)
        except Exception as exc:
            reporting_db.fail_run(run_id, _safe_error(exc))
            raise


def read_weekly_location_performance(week_start: date | None = None) -> dict:
    """Query loaded KPI rows. Does not recompute."""
    return reporting_db.read_weekly_location_performance(week_start)


def latest_weekly_performance_run() -> dict | None:
    """Newest run row, including a run that is still marked Running."""
    return reporting_db.latest_weekly_performance_run()


def _safe_error(exc: Exception) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if "://" in message or "password" in message.lower():
        return "The database connection failed before the week could be loaded."
    return message[:500]


def main(argv: list[str] | None = None) -> dict:
    args = list(sys.argv[1:] if argv is None else argv)
    week = date.fromisoformat(args[0]) if args else None
    result = request_weekly_location_performance_run(week)
    print(json.dumps({k: result[k] for k in result if k != "error_message" or result[k]}))
    if result.get("status") == "Failed":
        raise SystemExit(1)
    return result


if __name__ == "__main__":
    main()
