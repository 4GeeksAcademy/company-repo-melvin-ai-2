"""Weekly location KPIs, optional eval task, and reporting routes."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.pipelines import reporting_db  # noqa: E402
from data.pipelines.pipeline import weekly_location_performance  # noqa: E402
from data.process.weekly_location_performance import (  # noqa: E402
    aggregate_location_week,
    previous_completed_week,
)
from tests.factories import bearer  # noqa: E402

WEEK = date(2026, 9, 28)


def _event(event_id: str, event_type: str, **tags) -> dict:
    return {
        "event_id": event_id,
        "timestamp": "2026-09-29T15:00:00+00:00",
        "event_type": event_type,
        "tags": tags,
    }


def test_purchase_waste_ratio_and_counts_stay_in_one_currency():
    events = [
        _event(
            "in-1",
            "inbound_order_created",
            location_id=1,
            country="CO",
            currency="COP",
            quantity=10,
            unit_cost=1000,
        ),
        _event(
            "in-1",
            "inbound_order_created",
            location_id=1,
            country="CO",
            currency="COP",
            quantity=99,
            unit_cost=99,
        ),
        _event(
            "waste-1",
            "stock_waste_registered",
            location_id=1,
            country="CO",
            currency="COP",
            quantity=2,
            unit_cost=500,
        ),
        _event(
            "stock-1",
            "stock_threshold_triggered",
            location_id=1,
            country="CO",
            currency="COP",
        ),
        _event(
            "price-1",
            "ingredient_price_variance_detected",
            location_id=1,
            country="CO",
            currency="COP",
        ),
        _event(
            "out-1",
            "outbound_order_created",
            location_id=1,
            country="CO",
            currency="COP",
            quantity=4,
        ),
        _event(
            "us-1",
            "inbound_order_created",
            location_id=6,
            country="US",
            currency="USD",
            quantity=3,
            unit_cost=4,
        ),
    ]
    first = aggregate_location_week(WEEK, events)
    second = aggregate_location_week(WEEK, events)

    assert first == second
    by_location = {row["location_id"]: row for row in first["rows"]}
    colombia = by_location["1"]
    assert colombia["currency"] == "COP"
    assert colombia["total_purchase_cost"] == "10000.00"
    assert colombia["total_waste_cost"] == "1000.00"
    assert colombia["waste_ratio"] == "0.100000"
    assert colombia["stockout_events_count"] == 1
    assert colombia["price_alert_events_count"] == 1
    assert by_location["6"]["currency"] == "USD"
    assert by_location["6"]["total_purchase_cost"] == "12.00"
    assert first["outbound_events_count"] == 1
    assert "medellin-centro" not in by_location


def test_missing_cost_currency_mismatch_and_slug_are_skipped():
    events = [
        _event(
            "waste-old",
            "stock_waste_registered",
            location_id="2",
            country="CO",
            currency="COP",
            quantity=1,
        ),
        _event(
            "bad-fx",
            "inbound_order_created",
            location_id=2,
            country="CO",
            currency="USD",
            quantity=1,
            unit_cost=10,
        ),
        _event(
            "slug",
            "inbound_order_created",
            location_id="medellin-centro",
            country="CO",
            currency="COP",
            quantity=1,
            unit_cost=10,
        ),
        _event(
            "no-location",
            "stock_threshold_triggered",
            country="CO",
            currency="COP",
        ),
    ]
    result = aggregate_location_week(WEEK, events)
    assert result["rows"] == []
    assert result["events_skipped_missing_cost"] == 4
    assert result["records_read"] == 4


def test_zero_purchases_keep_waste_ratio_at_zero():
    events = [
        _event(
            "waste-only",
            "stock_waste_registered",
            location_id=3,
            country="US",
            currency="USD",
            quantity=2,
            unit_cost=5,
        )
    ]
    row = aggregate_location_week(WEEK, events)["rows"][0]
    assert row["total_purchase_cost"] == "0.00"
    assert row["total_waste_cost"] == "10.00"
    assert row["waste_ratio"] == "0"
    assert row["currency"] == "USD"


def test_upsert_replaces_the_location_week():
    assert "ON CONFLICT (location_id, week_start) DO UPDATE" in reporting_db.UPSERT_SQL


def test_previous_week_is_the_monday_before_this_one():
    assert previous_completed_week(date(2026, 10, 6)) == date(2026, 9, 28)
    assert previous_completed_week(date(2026, 10, 5)) == date(2026, 9, 28)


def test_eval_snapshot_failure_does_not_stop_load(monkeypatch):
    monkeypatch.setenv("BRASALAND_EVAL_SNAPSHOT_FAIL", "1")
    monkeypatch.setattr(reporting_db, "fetch_week_events", lambda _week: [])
    loaded: dict = {}

    def load_week(run_id, week_start, transformed):
        loaded["run_id"] = run_id
        loaded["rows"] = transformed["rows"]
        return {
            "run_id": run_id,
            "week_start": week_start.isoformat(),
            "status": "Completed",
            "started_at": "2026-10-06T11:00:00+00:00",
            "ended_at": "2026-10-06T11:00:01+00:00",
            "records_read": 0,
            "records_loaded": 0,
            "records_processed": 0,
            "events_skipped_missing_cost": 0,
            "error_message": "",
        }

    monkeypatch.setattr(reporting_db, "load_week", load_week)
    result = weekly_location_performance(WEEK, "run-1")
    assert loaded["run_id"] == "run-1"
    assert loaded["rows"] == []
    assert result["status"] == "Completed"


def test_reporting_routes_require_a_token_and_do_not_recompute(client, lucia_token, monkeypatch):
    monkeypatch.setattr(
        "reporting.router.latest_weekly_performance_run",
        lambda: {
            "run_id": "run-9",
            "week_start": "2026-09-28",
            "status": "Completed",
            "started_at": "2026-10-06T11:00:00+00:00",
            "ended_at": "2026-10-06T11:00:02+00:00",
            "records_read": 4,
            "records_loaded": 1,
            "records_processed": 4,
            "events_skipped_missing_cost": 0,
            "error_message": "",
        },
    )
    monkeypatch.setattr(
        "reporting.router.read_weekly_location_performance",
        lambda week_start=None: {
            "week_start": "2026-09-28",
            "locations": [
                {
                    "location_id": "1",
                    "country": "CO",
                    "total_purchase_cost": 10000,
                    "total_waste_cost": 1000,
                    "waste_ratio": 0.1,
                    "stockout_events_count": 1,
                    "price_alert_events_count": 1,
                    "currency": "COP",
                }
            ],
        },
    )
    started: dict = {}

    def start(week_start=None):
        started["week"] = week_start
        return {"run_id": "run-new", "status": "Completed", "week_start": "2026-09-28"}

    monkeypatch.setattr("reporting.router.request_weekly_location_performance_run", start)

    assert client.get("/reporting/pipeline-runs/latest").status_code == 401
    assert client.get("/reporting/weekly-location-performance").status_code == 401
    assert client.post("/reporting/pipeline-runs", json={}).status_code == 401

    headers = bearer(lucia_token)
    latest = client.get("/reporting/pipeline-runs/latest", headers=headers)
    assert latest.status_code == 200
    body = latest.json()
    assert body["status"] == "Completed"
    assert body["started_at"]
    assert body["ended_at"]
    assert body["records_processed"] == 4
    assert body["error_message"] == ""

    report = client.get("/reporting/weekly-location-performance", headers=headers)
    assert report.status_code == 200
    payload = report.json()
    assert payload["week_start"] == "2026-09-28"
    assert payload["locations"][0]["location_id"] == "1"
    assert payload["locations"][0]["currency"] == "COP"
    assert set(payload["locations"][0]) == {
        "location_id",
        "country",
        "total_purchase_cost",
        "total_waste_cost",
        "waste_ratio",
        "stockout_events_count",
        "price_alert_events_count",
        "currency",
    }

    manual = client.post(
        "/reporting/pipeline-runs",
        headers=headers,
        json={"week_start": "2026-09-28"},
    )
    assert manual.status_code == 200
    assert manual.json()["run_id"] == "run-new"
    assert started["week"] == date(2026, 9, 28)


def test_latest_run_404_when_nothing_has_been_recorded(client, lucia_token, monkeypatch):
    monkeypatch.setattr("reporting.router.latest_weekly_performance_run", lambda: None)
    response = client.get(
        "/reporting/pipeline-runs/latest",
        headers=bearer(lucia_token),
    )
    assert response.status_code == 404
    assert "weekly performance run" in response.json()["detail"]
