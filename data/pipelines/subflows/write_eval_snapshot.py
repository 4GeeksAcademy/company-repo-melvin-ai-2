"""Optional context file. Outbound volume is not a KPI."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from prefect import flow, task

ROOT = Path(__file__).resolve().parents[3]
EVAL_DIR = ROOT / "data" / "eval"


@task(name="write_weekly_eval_file")
def write_weekly_eval_file(week_start: date, transformed: dict) -> str:
    """Input: week and KPI rows. Output: path of the context file."""
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


@flow(name="write_eval_snapshot")
def write_eval_snapshot(week_start: date, transformed: dict) -> str:
    """Optional subflow. The main flow calls it with ``return_state=True``."""
    return write_weekly_eval_file(week_start, transformed)
