"""Aggregate one UTC week of telemetry into location KPIs.

Purchase cost and waste cost are ``quantity * unit_cost`` in the location
currency. COP and USD are never added into the same row. Outbound events are
counted for context and are not a KPI.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

COST_EVENTS = frozenset({"inbound_order_created", "stock_waste_registered"})
COUNTRY_CURRENCY = {"CO": "COP", "US": "USD"}
MONEY = Decimal("0.01")
RATIO = Decimal("0.000001")


def previous_completed_week(today: date | None = None) -> date:
    """Monday (UTC) of the ISO week that has already ended."""
    current = today or datetime.now(timezone.utc).date()
    this_monday = current - timedelta(days=current.weekday())
    return this_monday - timedelta(days=7)


def monday_of(day: date) -> date:
    """Normalize any day to the Monday of its ISO week."""
    return day - timedelta(days=day.weekday())


def aggregate_location_week(week_start: date, events: list[dict]) -> dict:
    """One KPI row per numeric ``location_id`` for ``week_start``.

    A repeated ``event_id`` is counted once. A cost event with no ``unit_cost``,
    a null location, or a country that disagrees with the currency is left out
    of the sums and increments ``events_skipped_missing_cost``. That is the
    only skip counter on the run log, so every excluded event is recorded
    there. ``outbound_order_created`` is not a skip and not a KPI.
    """
    week = monday_of(week_start)
    seen: set[str] = set()
    buckets: dict[str, dict] = {}
    skipped = 0
    outbound = 0

    ordered = sorted(events, key=lambda event: str(event.get("event_id") or ""))
    for event in ordered:
        event_id = str(event.get("event_id") or "")
        if not event_id or event_id in seen:
            if event_id:
                continue
            skipped += 1
            continue
        seen.add(event_id)

        event_type = str(event.get("event_type") or "")
        if event_type == "outbound_order_created":
            outbound += 1
            continue

        tags = event.get("tags") if isinstance(event.get("tags"), dict) else {}
        location_id = _location_id(tags.get("location_id"))
        country = tags.get("country")
        if location_id is None or country not in COUNTRY_CURRENCY:
            skipped += 1
            continue

        expected_currency = COUNTRY_CURRENCY[country]
        stated = tags.get("currency")
        if stated not in (None, "", expected_currency):
            skipped += 1
            continue

        contribution = _contribution(event_type, tags)
        if contribution is None:
            skipped += 1
            continue

        bucket = buckets.get(location_id)
        if bucket is None:
            bucket = {
                "location_id": location_id,
                "country": country,
                "week_start": week.isoformat(),
                "total_purchase_cost": Decimal("0"),
                "total_waste_cost": Decimal("0"),
                "stockout_events_count": 0,
                "price_alert_events_count": 0,
                "currency": expected_currency,
            }
            buckets[location_id] = bucket
        elif bucket["country"] != country:
            skipped += 1
            continue

        kind, amount = contribution
        if kind == "purchase":
            bucket["total_purchase_cost"] += amount
        elif kind == "waste":
            bucket["total_waste_cost"] += amount
        elif kind == "stockout":
            bucket["stockout_events_count"] += 1
        elif kind == "price_alert":
            bucket["price_alert_events_count"] += 1

    rows = [_finish_row(bucket) for _, bucket in sorted(buckets.items())]
    return {
        "rows": rows,
        "events_skipped_missing_cost": skipped,
        "records_read": len(events),
        "outbound_events_count": outbound,
    }


def _finish_row(bucket: dict) -> dict:
    purchase = bucket["total_purchase_cost"]
    waste = bucket["total_waste_cost"]
    ratio = Decimal("0") if purchase == 0 else (waste / purchase).quantize(RATIO)
    return {
        "location_id": bucket["location_id"],
        "country": bucket["country"],
        "week_start": bucket["week_start"],
        "total_purchase_cost": format(purchase.quantize(MONEY), "f"),
        "total_waste_cost": format(waste.quantize(MONEY), "f"),
        "waste_ratio": format(ratio, "f"),
        "stockout_events_count": bucket["stockout_events_count"],
        "price_alert_events_count": bucket["price_alert_events_count"],
        "currency": bucket["currency"],
    }


def _location_id(value: object) -> str | None:
    """Reporting stores the kitchen number as text. Slugs are not location ids."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return str(value) if value > 0 else None
    if isinstance(value, float) and value.is_integer() and value > 0:
        return str(int(value))
    text = str(value).strip()
    if text.isdigit() and int(text) > 0:
        return str(int(text))
    return None


def _contribution(event_type: str, tags: dict) -> tuple[str, Decimal] | None:
    if event_type in COST_EVENTS:
        amount = _line_cost(tags.get("quantity"), tags.get("unit_cost"))
        if amount is None:
            return None
        kind = "purchase" if event_type == "inbound_order_created" else "waste"
        return kind, amount
    if event_type == "stock_threshold_triggered":
        return "stockout", Decimal("0")
    if event_type == "ingredient_price_variance_detected":
        return "price_alert", Decimal("0")
    return None


def _line_cost(quantity: object, unit_cost: object) -> Decimal | None:
    if quantity is None or unit_cost is None or unit_cost == "":
        return None
    try:
        qty = Decimal(str(quantity))
        cost = Decimal(str(unit_cost))
    except (InvalidOperation, ValueError):
        return None
    if qty < 0 or cost < 0:
        return None
    return (qty * cost).quantize(MONEY)
