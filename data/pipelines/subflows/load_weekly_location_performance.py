"""Upsert the weekly location KPI rows."""

from __future__ import annotations

from datetime import date

from prefect import flow, task

from data.pipelines import reporting_db

# Three tries cover a brief Supabase pooler blip. Five seconds gives the
# pooler time to hand back a live connection before the next attempt.
_DB_RETRIES = 3
_DB_RETRY_DELAY_SECONDS = 5


@task(
    name="upsert_weekly_location_performance",
    retries=_DB_RETRIES,
    retry_delay_seconds=_DB_RETRY_DELAY_SECONDS,
)
def upsert_weekly_location_performance(
    run_id: str, week_start: date, transformed: dict
) -> dict:
    """Input: run id, week, and KPI rows. Output: the completed run record."""
    return reporting_db.load_week(run_id, week_start, transformed)


@flow(name="load_weekly_location_performance")
def load_weekly_location_performance(
    run_id: str, week_start: date, transformed: dict
) -> dict:
    """Subflow. Replaces the location rows for this week. It does not add a second copy."""
    return upsert_weekly_location_performance(run_id, week_start, transformed)
