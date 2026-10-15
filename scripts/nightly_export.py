"""Export one UTC day of telemetry and start the weekly location pipeline.

Run from the repo root with the API environment:

    services/api/.venv/bin/python scripts/nightly_export.py

``TARGET_DATE=YYYY-MM-DD`` overrides yesterday. The script is a separate
process from FastAPI. Crontab runs it; the API process does not.

Cron expression, UTC: ``0 2 * * *``

    CRON_TZ=UTC
    0 2 * * * cd /path/to/company-repo && /path/to/services/api/.venv/bin/python scripts/nightly_export.py

02:00 UTC is after the previous calendar day has closed. The host crontab is
the trigger so a long export cannot block an API worker.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.job_runner import JOB_NAME  # noqa: E402
from services.job_runner import (  # noqa: E402
    begin_run,
    ensure_job_runs_table,
    fail_if_processing,
    fetch_telemetry_day,
    has_completed_for_date,
    has_processing_lock,
    mark_completed,
    mark_failed,
    public_error,
)

RAW_DIR = ROOT / "data" / "raw"
CSV_COLUMNS = (
    "event_id",
    "timestamp",
    "session_id",
    "user_id",
    "event_type",
    "service",
    "request_id",
    "tags",
)
PIPELINE = ROOT / "data" / "pipelines" / "pipeline.py"

logger = logging.getLogger("brasaland.nightly_export")


class _JobLog(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = dict(self.extra)
        extra.update(kwargs.pop("extra", None) or {})
        kwargs["extra"] = extra
        return msg, kwargs


def resolve_target_date(environ: dict[str, str] | None = None, today: date | None = None) -> date:
    """Yesterday in UTC, or ``TARGET_DATE`` when that variable is set."""
    from datetime import datetime, timezone

    source = os.environ if environ is None else environ
    current = today or datetime.now(timezone.utc).date()
    raw = (source.get("TARGET_DATE") or "").strip()
    if not raw:
        return current - timedelta(days=1)
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("TARGET_DATE must be YYYY-MM-DD") from exc


def csv_path(target_date: date, raw_dir: Path = RAW_DIR) -> Path:
    return raw_dir / f"telemetry_{target_date.isoformat()}.csv"


def export_csv(path: Path, rows: list[dict]) -> bool:
    """Write the backup snapshot when ``path`` is absent. Return True if written."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".csv.partial")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(_csv_row(row))
    temporary.replace(path)
    return True


def main(argv: list[str] | None = None) -> int:
    del argv
    log = _configure_logging()
    try:
        target_date = resolve_target_date()
    except ValueError as exc:
        log.error(str(exc), extra={"status": "failed"})
        return 1

    try:
        ensure_job_runs_table()
        if has_processing_lock(JOB_NAME):
            log.info(
                "cancelled; another nightly export is processing",
                extra={"status": "processing", "target_date": target_date.isoformat()},
            )
            return 0
        if has_completed_for_date(JOB_NAME, target_date):
            log.info(
                "skipped as duplicate",
                extra={"status": "completed", "target_date": target_date.isoformat()},
            )
            return 0
        run = begin_run(JOB_NAME, target_date)
        if run is None:
            log.info(
                "cancelled; another nightly export claimed the lock",
                extra={"status": "processing", "target_date": target_date.isoformat()},
            )
            return 0
    except Exception as exc:
        log.error(public_error(exc), extra={"status": "failed", "target_date": target_date.isoformat()})
        return 1

    run_id = run["id"]
    exit_code = 0
    try:
        log.info(
            "start",
            extra={"status": "processing", "target_date": target_date.isoformat()},
        )
        path = csv_path(target_date)
        if export_csv(path, fetch_telemetry_day(target_date)):
            log.info(
                "wrote %s",
                path.name,
                extra={"status": "processing", "target_date": target_date.isoformat()},
            )
        else:
            log.info(
                "csv already present",
                extra={"status": "processing", "target_date": target_date.isoformat()},
            )
        _run_pipeline(target_date)
        mark_completed(run_id)
        log.info(
            "finish",
            extra={"status": "completed", "target_date": target_date.isoformat()},
        )
    except Exception as exc:
        message = public_error(exc)
        mark_failed(run_id, message)
        log.error(message, extra={"status": "failed", "target_date": target_date.isoformat()})
        exit_code = 1
    finally:
        try:
            fail_if_processing(
                run_id,
                "The nightly export stopped before it recorded a final status.",
            )
        except Exception as exc:
            log.error(
                public_error(exc),
                extra={"status": "failed", "target_date": target_date.isoformat()},
            )
            exit_code = 1
    return exit_code


def _run_pipeline(target_date: date) -> None:
    """Start the Milestone 6 CLI in a child process. It reads the database, not the CSV."""
    completed = subprocess.run(
        [sys.executable, str(PIPELINE), target_date.isoformat()],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "pipeline exited").strip()
        if "://" in detail or "password" in detail.lower():
            detail = "The pipeline exited before the nightly export finished."
        elif detail:
            detail = detail.splitlines()[-1]
        raise RuntimeError(detail[:500] or "pipeline exited")


def _csv_row(row: dict) -> dict:
    tags = row.get("tags")
    if not isinstance(tags, str):
        tags = json.dumps(tags if tags is not None else {}, sort_keys=True)
    timestamp = row.get("timestamp")
    return {
        "event_id": row.get("event_id") or "",
        "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else (timestamp or ""),
        "session_id": row.get("session_id") or "",
        "user_id": row.get("user_id") or "",
        "event_type": row.get("event_type") or "",
        "service": row.get("service") or "",
        "request_id": row.get("request_id") or "",
        "tags": tags,
    }


def _configure_logging() -> _JobLog:
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s job_name=%(job_name)s status=%(status)s %(message)s"
            )
        )
        logger.addHandler(handler)
    return _JobLog(logger, {"job_name": JOB_NAME, "status": "pending"})


if __name__ == "__main__":
    raise SystemExit(main())
