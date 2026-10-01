"""Operational report: Pandas metrics, one window, 60-second cache."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_SERVICES = Path(__file__).resolve().parents[2]
if str(_SERVICES) not in sys.path:
    sys.path.insert(0, str(_SERVICES))

import pandas as pd
import pytest

from app.telemetry.report import report_cache


@pytest.fixture(autouse=True)
def clear_report_cache():
    report_cache.clear()
    yield
    report_cache.clear()


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "timestamp": "2026-09-29T22:00:00-05:00",
                "event_type": "auth_login_failed",
                "tags": {"failure_code": "invalid_credentials"},
            },
            {
                "timestamp": "2026-09-30T03:10:00Z",
                "event_type": "auth_login_succeeded",
                "tags": {"role": "admin"},
            },
            {
                "timestamp": "2026-09-30T03:20:00Z",
                "event_type": "auth_session_expired",
                "tags": {"failure_code": "token_expired"},
            },
            {
                "timestamp": "2026-09-30T04:00:00Z",
                "event_type": "client_error_uncaught",
                "tags": {"error_name": "TypeError", "route": "/suppliers"},
            },
            {
                "timestamp": "2026-09-30T04:05:00Z",
                "event_type": "inventory_order_validation_failed",
                "tags": {"location_id": 1},
            },
            {
                "timestamp": "2026-09-30T04:06:00Z",
                "event_type": "direct_stock_edit_rejected",
                "tags": {"location_id": 1},
            },
            {
                "timestamp": "2026-09-30T04:07:00Z",
                "event_type": "stock_threshold_edit_rejected",
                "tags": {"location_id": 2},
            },
            {
                "timestamp": "2026-09-30T05:00:00Z",
                "event_type": "backoffice_page_viewed",
                "tags": {"route": "/"},
            },
            {
                "timestamp": "2026-09-30T05:01:00Z",
                "event_type": "api_latency_recorded",
                "tags": {
                    "route": "/inventory/products",
                    "http_method": "GET",
                    "http_status": 200,
                    "duration_ms": 40,
                },
            },
            {
                "timestamp": "2026-09-30T05:02:00Z",
                "event_type": "api_latency_recorded",
                "tags": {
                    "route": "/inventory/products",
                    "http_method": "GET",
                    "http_status": 200,
                    "duration_ms": 60,
                },
            },
            {
                "timestamp": "2026-09-30T05:03:00Z",
                "event_type": "api_latency_recorded",
                "tags": {
                    "route": "/auth/login",
                    "http_method": "POST",
                    "http_status": 200,
                    "duration_ms": 100,
                },
            },
            {
                "timestamp": "2026-09-29T12:00:00Z",
                "event_type": "inbound_order_created",
                "tags": {"location_id": 1, "country": "CO"},
            },
        ]
    )


def _install_frame(monkeypatch):
    calls: list[tuple] = []

    def fake_load(start, end, event_types):
        calls.append((start, end, event_types))
        frame = _frame()
        if event_types:
            frame = frame.loc[frame["event_type"].isin(event_types)]
        return frame.copy()

    monkeypatch.setattr("telemetry.analysis.load_events", fake_load)
    return calls


def test_events_per_day_uses_utc_before_grouping(monkeypatch):
    _install_frame(monkeypatch)
    from telemetry.analysis import events_per_day

    start = datetime(2026, 9, 23, tzinfo=timezone.utc)
    end = datetime(2026, 9, 30, 6, tzinfo=timezone.utc)
    rows = events_per_day(start, end)
    assert rows == events_per_day(start, end)
    by_day = {row["date"]: row["event_count"] for row in rows}
    # 22:00 in UTC-5 is 03:00 the next day in UTC, so it joins 2026-09-30.
    assert by_day == {"2026-09-29": 1, "2026-09-30": 11}


def test_error_rate_keeps_every_failure_event(monkeypatch):
    _install_frame(monkeypatch)
    from telemetry.analysis import ERROR_EVENT_TYPES, error_rate_by_type

    rows = error_rate_by_type(
        datetime(2026, 9, 23, tzinfo=timezone.utc),
        datetime(2026, 9, 30, 6, tzinfo=timezone.utc),
    )
    found = {row["event_type"] for row in rows}
    assert found == set(ERROR_EVENT_TYPES)
    failed = next(row for row in rows if row["event_type"] == "auth_login_failed")
    assert failed["date"] == "2026-09-30"
    assert failed["error_count"] == 1
    assert failed["total"] == 11
    assert failed["error_rate"] == pytest.approx(1 / 11)
    assert all(isinstance(row, dict) for row in rows)


def test_auth_failure_rate_is_failed_over_attempts(monkeypatch):
    _install_frame(monkeypatch)
    from telemetry.analysis import auth_failure_rate

    rows = auth_failure_rate(
        datetime(2026, 9, 23, tzinfo=timezone.utc),
        datetime(2026, 9, 30, 6, tzinfo=timezone.utc),
    )
    assert rows == [
        {
            "date": "2026-09-30",
            "failed": 1,
            "attempts": 2,
            "auth_failure_rate": 0.5,
        }
    ]


def test_latency_is_mean_duration_by_route(monkeypatch):
    _install_frame(monkeypatch)
    from telemetry.analysis import latency_by_route

    rows = latency_by_route(
        datetime(2026, 9, 23, tzinfo=timezone.utc),
        datetime(2026, 9, 30, 6, tzinfo=timezone.utc),
    )
    assert rows == [
        {
            "date": "2026-09-30",
            "route": "/auth/login",
            "mean_duration_ms": 100.0,
        },
        {
            "date": "2026-09-30",
            "route": "/inventory/products",
            "mean_duration_ms": 50.0,
        },
    ]


def test_load_filters_time_and_event_type_in_sql(monkeypatch):
    captured: dict = {}

    class Connection:
        def execute(self, statement, params):
            captured["sql"] = str(statement)
            captured["params"] = params

            class Result:
                def mappings(self):
                    return self

                def all(self):
                    return []

            return Result()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class Engine:
        def connect(self):
            return Connection()

    monkeypatch.setattr("telemetry.analysis.get_engine", lambda: Engine())
    from telemetry.analysis import load_events

    start = datetime(2026, 9, 23, tzinfo=timezone.utc)
    end = datetime(2026, 9, 30, tzinfo=timezone.utc)
    frame = load_events(start, end, ("auth_login_failed", "client_error_uncaught"))
    assert list(frame.columns) == ["timestamp", "event_type", "tags"]
    assert "timestamp >= :start" in captured["sql"]
    assert "timestamp < :end" in captured["sql"]
    assert "event_type = ANY(:event_types)" in captured["sql"]
    assert "tags" not in captured["sql"].split("WHERE", 1)[1]
    assert captured["params"]["start"] == start
    assert captured["params"]["end"] == end
    assert captured["params"]["event_types"] == [
        "auth_login_failed",
        "client_error_uncaught",
    ]


def test_report_defaults_to_seven_days_and_reuses_cache(client, monkeypatch):
    calls = _install_frame(monkeypatch)
    first = client.get("/telemetry/report")
    second = client.get("/telemetry/report")
    assert first.status_code == 200
    assert second.json() == first.json()
    body = first.json()
    assert set(body) == {"period", "metrics"}
    assert set(body["metrics"]) == {
        "events_per_day",
        "error_rate_by_type",
        "auth_failure_rate",
        "latency_by_route",
    }
    start = datetime.fromisoformat(body["period"]["from"])
    end = datetime.fromisoformat(body["period"]["to"])
    assert end - start == timedelta(days=7)
    windows = {(call[0], call[1]) for call in calls}
    assert windows == {(start, end)}
    assert len(calls) == 4
    client.get("/telemetry/report")
    assert len(calls) == 4


def test_report_cache_misses_when_the_window_changes(client, monkeypatch):
    calls = _install_frame(monkeypatch)
    client.get("/telemetry/report")
    response = client.get(
        "/telemetry/report",
        params={
            "start_date": "2026-09-01T00:00:00Z",
            "end_date": "2026-09-08T00:00:00Z",
        },
    )
    assert response.status_code == 200
    assert response.json()["period"]["from"].startswith("2026-09-01")
    assert response.json()["period"]["to"].startswith("2026-09-08")
    assert len(calls) == 8


def test_report_rejects_a_reversed_window(client):
    response = client.get(
        "/telemetry/report",
        params={
            "start_date": "2026-09-08T00:00:00Z",
            "end_date": "2026-09-01T00:00:00Z",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "start_date must be before end_date."
