"""Operational metrics for Brasaland telemetry_events.

Each function loads a time window from SQL, refines rows in Pandas, converts
timestamps to UTC, then groups and aggregates. None of them writes, and none
of them chooses its own default window.
"""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd
from sqlalchemy import String, bindparam, text
from sqlalchemy.dialects.postgresql import ARRAY

from app.inventory.db import get_engine

# Failures, rejections, and client errors. Login success and inventory
# orders are not errors; login success is only the denominator of auth_failure_rate.
ERROR_EVENT_TYPES = (
    "auth_login_failed",
    "auth_session_expired",
    "client_error_uncaught",
    "direct_stock_edit_rejected",
    "inventory_order_validation_failed",
    "stock_threshold_edit_rejected",
)
LOGIN_EVENT_TYPES = ("auth_login_failed", "auth_login_succeeded")
LATENCY_EVENT_TYPE = ("api_latency_recorded",)

_WINDOW = text(
    """
    SELECT timestamp, event_type, tags
    FROM telemetry_events
    WHERE timestamp >= :start AND timestamp < :end
    """
)
_WINDOW_TYPES = text(
    """
    SELECT timestamp, event_type, tags
    FROM telemetry_events
    WHERE timestamp >= :start AND timestamp < :end
      AND event_type = ANY(:event_types)
    """
).bindparams(bindparam("event_types", type_=ARRAY(String)))
_COLUMNS = ["timestamp", "event_type", "tags"]


def load_events(
    start: datetime,
    end: datetime,
    event_types: tuple[str, ...] | None,
) -> pd.DataFrame:
    """Load one window. The end is exclusive. Tags are not filtered in SQL."""
    params: dict = {"start": start, "end": end}
    statement = _WINDOW
    if event_types:
        statement = _WINDOW_TYPES
        params["event_types"] = list(event_types)
    engine = get_engine()
    with engine.connect() as connection:
        rows = connection.execute(statement, params).mappings().all()
    return pd.DataFrame(rows, columns=_COLUMNS)


def events_per_day(start: datetime, end: datetime) -> list[dict]:
    """How many events the pipeline stored on each UTC day."""
    frame = load_events(start, end, None)
    if frame.empty:
        return []
    frame = _with_utc_date(frame)
    grouped = frame.groupby("date", as_index=False).agg(event_count=("event_type", "count"))
    return _records(grouped.sort_values("date"))


def error_rate_by_type(start: datetime, end: datetime) -> list[dict]:
    """Share of the day's events that belong to each error event type."""
    frame = load_events(start, end, None)
    if frame.empty:
        return []
    frame = frame.copy()
    frame["is_error"] = frame["event_type"].isin(ERROR_EVENT_TYPES)
    frame = _with_utc_date(frame)
    totals = frame.groupby("date", as_index=False).agg(total=("event_type", "count"))
    errors = (
        frame.loc[frame["is_error"]]
        .groupby(["date", "event_type"], as_index=False)
        .agg(error_count=("event_type", "count"))
    )
    if errors.empty:
        return []
    grouped = errors.merge(totals, on="date", how="left")
    grouped["error_rate"] = grouped["error_count"] / grouped["total"]
    columns = ["date", "event_type", "error_count", "total", "error_rate"]
    return _records(grouped[columns].sort_values(["date", "event_type"]))


def auth_failure_rate(start: datetime, end: datetime) -> list[dict]:
    """Failed logins divided by failed plus succeeded logins, per UTC day."""
    frame = load_events(start, end, LOGIN_EVENT_TYPES)
    if frame.empty:
        return []
    frame = frame.copy()
    frame["is_failed"] = frame["event_type"].eq("auth_login_failed")
    frame = _with_utc_date(frame)
    grouped = frame.groupby("date", as_index=False).agg(
        failed=("is_failed", "sum"),
        attempts=("event_type", "count"),
    )
    grouped["auth_failure_rate"] = grouped["failed"] / grouped["attempts"]
    columns = ["date", "failed", "attempts", "auth_failure_rate"]
    return _records(grouped[columns].sort_values("date"))


def latency_by_route(start: datetime, end: datetime) -> list[dict]:
    """Mean api_latency_recorded duration, grouped by UTC day and route."""
    frame = load_events(start, end, LATENCY_EVENT_TYPE)
    if frame.empty:
        return []
    frame = frame.reset_index(drop=True).copy()
    tags = pd.json_normalize(frame["tags"].map(_tag_dict))
    frame["route"] = tags["route"] if "route" in tags.columns else pd.NA
    frame["duration_ms"] = pd.to_numeric(
        tags["duration_ms"] if "duration_ms" in tags.columns else pd.NA,
        errors="coerce",
    )
    frame = frame.dropna(subset=["route", "duration_ms"])
    if frame.empty:
        return []
    frame = _with_utc_date(frame)
    grouped = frame.groupby(["date", "route"], as_index=False).agg(
        mean_duration_ms=("duration_ms", "mean")
    )
    return _records(grouped.sort_values(["date", "route"]))


def build_report(start: datetime, end: datetime) -> dict:
    """Run every metric on one window. The caller decides that window."""
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "metrics": {
            "events_per_day": events_per_day(start, end),
            "error_rate_by_type": error_rate_by_type(start, end),
            "auth_failure_rate": auth_failure_rate(start, end),
            "latency_by_route": latency_by_route(start, end),
        },
    }


def _with_utc_date(frame: pd.DataFrame) -> pd.DataFrame:
    prepared = frame.copy()
    prepared["timestamp"] = pd.to_datetime(prepared["timestamp"], utc=True)
    prepared["date"] = prepared["timestamp"].dt.date
    return prepared


def _tag_dict(value: object) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _records(frame: pd.DataFrame) -> list[dict]:
    if frame.empty:
        return []
    ready = frame.copy()
    if "date" in ready.columns:
        ready["date"] = ready["date"].astype(str)
    return json.loads(ready.to_json(orient="records"))
