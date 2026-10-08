"""Turn one week's events into Purchase Cost, Waste Cost, Waste Ratio, Stockout Frequency, and Price Alert Frequency."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

from prefect import flow, task

from data.process.weekly_location_performance import aggregate_location_week


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
    name="aggregate_location_week_kpis",
    cache_key_fn=_transform_cache_key,
    cache_expiration=timedelta(hours=1),
)
def aggregate_location_week_kpis(week_start: date, events: list[dict]) -> dict:
    """Input: week and events. Output: one KPI row per location."""
    return aggregate_location_week(week_start, events)


@flow(name="transform_location_week")
def transform_location_week(week_start: date, events: list[dict]) -> dict:
    """Subflow. Purchase, waste, stockout, and price-alert totals for the week."""
    return aggregate_location_week_kpis(week_start, events)
