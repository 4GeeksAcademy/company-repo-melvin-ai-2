"""Status rows for the nightly telemetry export.

The nightly script owns these rows. ``reporting.weekly_performance_run`` stays
the Milestone 6 pipeline log. This module does not import FastAPI.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import IntegrityError

JOB_NAME = "nightly_export"
ROOT = Path(__file__).resolve().parents[1]
API_ENV = ROOT / "services" / "api" / ".env"

_engine: Engine | None = None

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS job_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_name text NOT NULL,
  target_date date NOT NULL,
  status text NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
  started_at timestamptz,
  finished_at timestamptz,
  error_message text NOT NULL DEFAULT '',
  created_at timestamptz NOT NULL DEFAULT now()
)
"""

_CREATE_LOOKUP_INDEX = """
CREATE INDEX IF NOT EXISTS job_runs_job_name_target_date_idx
  ON job_runs (job_name, target_date)
"""

# One processing row per job name. The status value is the lock. There is no
# second lock table or lock column.
_CREATE_PROCESSING_INDEX = """
CREATE UNIQUE INDEX IF NOT EXISTS job_runs_one_processing_per_job
  ON job_runs (job_name)
  WHERE status = 'processing'
"""


def ensure_job_runs_table() -> None:
    """Create ``job_runs`` when the nightly script starts."""
    with get_engine().begin() as conn:
        conn.execute(text(_CREATE_TABLE))
        conn.execute(text(_CREATE_LOOKUP_INDEX))
        conn.execute(text(_CREATE_PROCESSING_INDEX))


def has_processing_lock(job_name: str) -> bool:
    """True when this job already has a row in ``processing``."""
    with get_engine().connect() as conn:
        return _has_processing_lock(conn, job_name)


def has_completed_for_date(job_name: str, target_date: date) -> bool:
    """True when this job already completed for that UTC date."""
    with get_engine().connect() as conn:
        return _has_completed_for_date(conn, job_name, target_date)


def begin_run(job_name: str, target_date: date) -> dict | None:
    """Insert ``pending``, then move that same row to ``processing``.

    Returns None when another row for ``job_name`` is already processing, or
    when this ``target_date`` is already completed. The insert is rolled back
    in both cases, so a cancelled start does not leave a row behind.
    """
    try:
        with get_engine().begin() as conn:
            if _has_processing_lock(conn, job_name) or _has_completed_for_date(
                conn, job_name, target_date
            ):
                return None
            created = conn.execute(
                text(
                    """
                    INSERT INTO job_runs (job_name, target_date, status)
                    VALUES (:job_name, :target_date, 'pending')
                    RETURNING id
                    """
                ),
                {"job_name": job_name, "target_date": target_date},
            ).one()
            claimed = conn.execute(
                text(
                    """
                    UPDATE job_runs
                    SET status = 'processing', started_at = now()
                    WHERE id = :id
                      AND status = 'pending'
                      AND NOT EXISTS (
                        SELECT 1 FROM job_runs
                        WHERE job_name = :job_name
                          AND status = 'processing'
                          AND id <> :id
                      )
                    RETURNING id, job_name, target_date, status, started_at, created_at
                    """
                ),
                {"id": created.id, "job_name": job_name},
            ).mappings().first()
            if claimed is None:
                raise _ClaimLost()
            return _row(claimed)
    except (IntegrityError, _ClaimLost):
        return None


def mark_completed(run_id: UUID) -> None:
    """Close a processing row as ``completed``."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                UPDATE job_runs
                SET status = 'completed', finished_at = now(), error_message = ''
                WHERE id = :id AND status = 'processing'
                """
            ),
            {"id": run_id},
        )


def mark_failed(run_id: UUID, error_message: str) -> None:
    """Close a processing row as ``failed`` and store the exception text."""
    with get_engine().begin() as conn:
        conn.execute(
            text(
                """
                UPDATE job_runs
                SET status = 'failed',
                    finished_at = now(),
                    error_message = :error_message
                WHERE id = :id AND status = 'processing'
                """
            ),
            {"id": run_id, "error_message": error_message[:500]},
        )


def fail_if_processing(run_id: UUID, error_message: str) -> None:
    """Move a row that is still ``processing`` to ``failed``."""
    mark_failed(run_id, error_message)


def public_error(exc: BaseException) -> str:
    """Exception text safe to store. Connection URLs are not kept."""
    message = f"{type(exc).__name__}: {exc}"
    if "://" in message or "password" in message.lower():
        return "The database connection failed before the nightly export finished."
    return message[:500]


def fetch_telemetry_day(target_date: date) -> list[dict]:
    """Read one UTC calendar day from ``telemetry_events``. The table is not modified."""
    start = datetime.fromisoformat(f"{target_date.isoformat()}T00:00:00+00:00")
    end = start + timedelta(days=1)
    with get_engine().connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT event_id, timestamp, session_id, user_id, event_type,
                       service, request_id, tags
                FROM telemetry_events
                WHERE timestamp >= :start AND timestamp < :end
                ORDER BY timestamp, event_id
                """
            ),
            {"start": start, "end": end},
        ).mappings()
        return [dict(row) for row in rows]


def get_engine() -> Engine:
    """Open ``DATABASE_URL`` from the API env file. The password is not logged."""
    global _engine
    if _engine is None:
        if API_ENV.exists():
            load_dotenv(API_ENV)
        url = _database_url(os.getenv("DATABASE_URL") or "")
        if not url:
            raise RuntimeError(
                "Missing DATABASE_URL. Set it in services/api/.env before the nightly export."
            )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


def _has_processing_lock(conn: Connection, job_name: str) -> bool:
    found = conn.execute(
        text(
            """
            SELECT 1 FROM job_runs
            WHERE job_name = :job_name AND status = 'processing'
            LIMIT 1
            """
        ),
        {"job_name": job_name},
    ).first()
    return found is not None


def _has_completed_for_date(conn: Connection, job_name: str, target_date: date) -> bool:
    found = conn.execute(
        text(
            """
            SELECT 1 FROM job_runs
            WHERE job_name = :job_name
              AND target_date = :target_date
              AND status = 'completed'
            LIMIT 1
            """
        ),
        {"job_name": job_name, "target_date": target_date},
    ).first()
    return found is not None


def _row(mapping) -> dict:
    row = dict(mapping)
    if isinstance(row.get("target_date"), datetime):
        row["target_date"] = row["target_date"].date()
    return row


def _database_url(url: str) -> str:
    """Match the pooler URI encoding used by the inventory engine."""
    url = (url or "").strip()
    if not url or url.startswith("sqlite"):
        return url
    if "://" in url and "@" in url:
        scheme, rest = url.split("://", 1)
        creds, hostpart = rest.split("@", 1)
        if ":" in creds:
            user, password = creds.split(":", 1)
            if password.startswith("[") and password.endswith("]") and len(password) > 2:
                password = password[1:-1]
            url = f"{scheme}://{user}:{quote(password, safe='')}@{hostpart}"
    if "sslmode" not in url:
        url = f"{url}{'&' if '?' in url else '?'}sslmode=require"
    return url


class _ClaimLost(Exception):
    """The pending row could not move to processing."""
