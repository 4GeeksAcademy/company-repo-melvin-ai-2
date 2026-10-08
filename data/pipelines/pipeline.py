"""Weekly Location Cost & Waste Report.

Schedule: Monday 11:00 UTC (06:00 Colombia, 07:00 Florida). The run recomputes
the ISO week that just ended.

From the repo root, with the API environment:

    python data/pipelines/pipeline.py

An optional ``YYYY-MM-DD`` argument recomputes that week. The connection is
``DATABASE_URL`` (Prefect block ``brasaland-supabase``). This file does not
print or store the password.

The stage work lives in ``data/pipelines/subflows/``. This file only starts
those subflows and records the run.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Prefect 3 starts a local API the first time a flow runs. The default 20s
# wait is tight on a cold start, so give that process a minute.
os.environ.setdefault("PREFECT_SERVER_EPHEMERAL_STARTUP_TIMEOUT_SECONDS", "60")

from prefect import flow  # noqa: E402
from prefect.states import State  # noqa: E402

from data.pipelines import reporting_db  # noqa: E402
from data.pipelines.subflows import (  # noqa: E402
    extract_weekly_events,
    load_weekly_location_performance,
    transform_location_week,
    write_eval_snapshot,
)
from data.process.weekly_location_performance import (  # noqa: E402
    monday_of,
    previous_completed_week,
)

logger = logging.getLogger("brasaland.pipeline")


@flow(name="weekly_location_performance")
def weekly_location_performance(week_start: date, run_id: str) -> dict:
    """Call the stage subflows in order. This flow does not query or sum.

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
