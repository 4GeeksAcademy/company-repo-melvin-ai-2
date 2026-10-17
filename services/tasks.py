"""Async weekly location pipeline. The message is the week date, not the events."""

from __future__ import annotations

import logging
import sys
import time
from datetime import date
from pathlib import Path

from celery import Task

from services.celery_app import app
from services.task_dlq import record_dead_letter

logger = logging.getLogger("brasaland.tasks")

ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "services" / "api"
for entry in (str(ROOT), str(API_ROOT)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from data.pipelines.pipeline import (  # noqa: E402
    request_weekly_location_performance_run,
)

# Three retries after the first failure. Backoff starts at 2 seconds and doubles.
_MAX_RETRIES = 3


class _WeeklyTask(Task):
    """Move the task to the dead-letter queue only after the last retry."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        retries = int(getattr(self.request, "retries", 0) or 0)
        if retries < _MAX_RETRIES:
            return
        record_dead_letter(task_id, retries + 1, _safe_error(exc))


@app.task(
    bind=True,
    base=_WeeklyTask,
    name="brasaland.run_weekly_location_performance",
    autoretry_for=(Exception,),
    retry_backoff=2,
    retry_backoff_max=60,
    retry_jitter=False,
    max_retries=_MAX_RETRIES,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=150,
    time_limit=180,
)
def run_weekly_location_performance(self, week_start: str | None = None) -> dict:
    """Rebuild one location week. ``week_start`` is an ISO date or null."""
    started = time.perf_counter()
    attempt = int(self.request.retries) + 1
    task_id = self.request.id or ""
    try:
        week = date.fromisoformat(week_start) if week_start else None
        result = request_weekly_location_performance_run(week)
    except Exception as exc:
        duration_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "task_id=%s attempt=%s status=failure duration_ms=%.1f",
            task_id,
            attempt,
            duration_ms,
        )
        logger.error(
            "task_id=%s attempt=%s status=failure error=%s",
            task_id,
            attempt,
            _safe_error(exc),
        )
        raise
    duration_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "task_id=%s attempt=%s status=success duration_ms=%.1f",
        task_id,
        attempt,
        duration_ms,
    )
    return result


def _safe_error(exc: BaseException) -> str:
    message = f"{type(exc).__name__}: {exc}"
    if "://" in message or "password" in message.lower():
        return f"{type(exc).__name__}: the database connection failed"
    return message
