"""Read one UTC week of Brasaland telemetry events."""

from __future__ import annotations

from datetime import date

from prefect import flow, task

from data.pipelines import reporting_db

# Three tries cover a brief Supabase pooler blip. Five seconds gives the
# pooler time to hand back a live connection before the next attempt.
_DB_RETRIES = 3
_DB_RETRY_DELAY_SECONDS = 5


@task(
    name="read_weekly_telemetry_events",
    retries=_DB_RETRIES,
    retry_delay_seconds=_DB_RETRY_DELAY_SECONDS,
)
def read_weekly_telemetry_events(week_start: date) -> list[dict]:
    """Input: Monday of the week. Output: events for that half-open UTC week."""
    return reporting_db.fetch_week_events(week_start)


@flow(name="extract_weekly_events")
def extract_weekly_events(week_start: date) -> list[dict]:
    """Subflow. The caller passes ``week_start``. This flow does not share state."""
    return read_weekly_telemetry_events(week_start)
