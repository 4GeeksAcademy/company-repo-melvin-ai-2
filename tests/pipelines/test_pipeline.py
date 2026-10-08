"""Isolated checks for transform_location_week. No database and no Prefect."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.process.weekly_location_performance import aggregate_location_week

WEEK = date(2026, 9, 28)


def _event(event_id: str, event_type: str, **tags) -> dict:
    return {
        "event_id": event_id,
        "timestamp": "2026-09-29T15:00:00+00:00",
        "event_type": event_type,
        "tags": tags,
    }


def test_transform_location_week_purchase_cost_waste_cost_and_waste_ratio():
    """Hand-calculated week: 10 * 1000 purchase, 2 * 500 waste, ratio 0.1."""
    result = aggregate_location_week(
        WEEK,
        [
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
                "waste-1",
                "stock_waste_registered",
                location_id=1,
                country="CO",
                currency="COP",
                quantity=2,
                unit_cost=500,
            ),
        ],
    )
    row = result["rows"][0]
    assert row["location_id"] == "1"
    assert row["country"] == "CO"
    assert row["currency"] == "COP"
    assert row["total_purchase_cost"] == "10000.00"
    assert row["total_waste_cost"] == "1000.00"
    assert row["waste_ratio"] == "0.100000"


def test_transform_location_week_stockout_and_price_alert_counts():
    """Waste with no purchases keeps Waste Ratio at 0. Counts are not money."""
    result = aggregate_location_week(
        WEEK,
        [
            _event(
                "waste-only",
                "stock_waste_registered",
                location_id=3,
                country="US",
                currency="USD",
                quantity=2,
                unit_cost=5,
            ),
            _event(
                "stock-1",
                "stock_threshold_triggered",
                location_id=3,
                country="US",
                currency="USD",
            ),
            _event(
                "stock-2",
                "stock_threshold_triggered",
                location_id=3,
                country="US",
                currency="USD",
            ),
            _event(
                "price-1",
                "ingredient_price_variance_detected",
                location_id=3,
                country="US",
                currency="USD",
            ),
        ],
    )
    row = result["rows"][0]
    assert row["total_purchase_cost"] == "0.00"
    assert row["total_waste_cost"] == "10.00"
    assert row["waste_ratio"] == "0"
    assert row["stockout_events_count"] == 2
    assert row["price_alert_events_count"] == 1
    assert row["currency"] == "USD"


def test_transform_location_week_skips_malformed_events():
    result = aggregate_location_week(
        WEEK,
        [
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
        ],
    )
    assert result["rows"] == []
    assert result["events_skipped_missing_cost"] == 3
