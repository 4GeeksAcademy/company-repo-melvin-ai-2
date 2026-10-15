"""Isolated checks for the nightly export. No database and no pipeline."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.nightly_export import csv_path, export_csv, resolve_target_date
from services.job_runner import public_error

TODAY = date(2026, 10, 14)


def test_target_date_defaults_to_yesterday_utc():
    assert resolve_target_date({}, TODAY) == date(2026, 10, 13)


def test_target_date_env_overrides_yesterday():
    assert resolve_target_date({"TARGET_DATE": "2026-09-28"}, TODAY) == date(2026, 9, 28)


def test_target_date_rejects_a_bad_override():
    try:
        resolve_target_date({"TARGET_DATE": "09-28-2026"}, TODAY)
    except ValueError as exc:
        assert "YYYY-MM-DD" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_export_writes_once_and_leaves_an_existing_file(tmp_path):
    path = csv_path(date(2026, 9, 28), tmp_path)
    row = {
        "event_id": "evt-1",
        "timestamp": "2026-09-28T15:00:00+00:00",
        "session_id": "s",
        "user_id": None,
        "event_type": "inbound_order_created",
        "service": "backoffice",
        "request_id": "r",
        "tags": {"location_id": "1", "currency": "COP"},
    }
    assert export_csv(path, [row]) is True
    first = path.read_text(encoding="utf-8")
    assert "event_id" in first.splitlines()[0]
    assert "evt-1" in first
    assert "currency" in first and "COP" in first
    assert export_csv(path, []) is False
    assert path.read_text(encoding="utf-8") == first


def test_public_error_drops_a_connection_url():
    message = public_error(RuntimeError("failed postgresql://user:secret@host/db"))
    assert "secret" not in message
    assert "postgresql" not in message


def test_modules_do_not_import_fastapi():
    assert "fastapi" not in sys.modules
