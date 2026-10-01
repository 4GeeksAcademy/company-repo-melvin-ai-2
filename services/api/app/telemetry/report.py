"""Cached GET /telemetry/report. The window is resolved once per cache miss."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SERVICES = Path(__file__).resolve().parents[3]
if str(_SERVICES) not in sys.path:
    sys.path.insert(0, str(_SERVICES))

from telemetry.analysis import build_report  # noqa: E402

from app.cache import TtlCache  # noqa: E402

REPORT_TTL_SECONDS = 60.0
report_cache = TtlCache()


class ReportWindowError(ValueError):
    """The requested window is not a usable UTC range."""


def report_for(start_date: str | None, end_date: str | None) -> dict:
    """Return the cached report for this query pair, or calculate it once."""
    key = f"{start_date or ''}|{end_date or ''}"
    cached = report_cache.get(key)
    if cached is not None:
        return cached
    start, end = resolve_period(start_date, end_date)
    payload = build_report(start, end)
    report_cache.set(key, payload, REPORT_TTL_SECONDS)
    return payload


def resolve_period(
    start_date: str | None, end_date: str | None
) -> tuple[datetime, datetime]:
    """Default a missing bound to the last 7 days, both in UTC."""
    end = _parse_iso(end_date, "end_date") if end_date else datetime.now(timezone.utc)
    start = (
        _parse_iso(start_date, "start_date") if start_date else end - timedelta(days=7)
    )
    if start >= end:
        raise ReportWindowError("start_date must be before end_date.")
    return start, end


def _parse_iso(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ReportWindowError(f"{label} must be an ISO 8601 timestamp.") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
