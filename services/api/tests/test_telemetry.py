"""Storage ingest accepts a loose batch and does not require a session."""

from app.telemetry.router import telemetry_endpoint
from app.telemetry.store import tags_for


def _event(event_id: str, event_type: str, properties: dict, **overrides):
    body = {
        "eventId": event_id,
        "timestamp": "2026-09-28T20:00:00Z",
        "sessionId": "sess-1",
        "userId": "7",
        "event_type": event_type,
        "schemaVersion": "1.0.0",
        "requestId": "req-1",
        "properties": properties,
    }
    body.update(overrides)
    return body


def test_mixed_batch_counts_rejections_without_failing(client, monkeypatch):
    saved: list[dict] = []

    def fake_insert(rows: list[dict]) -> int:
        saved.extend(rows)
        return len(rows)

    monkeypatch.setattr("app.telemetry.router.insert_batch", fake_insert)
    monkeypatch.setenv("TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events")
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                _event(
                    "550e8400-e29b-41d4-a716-446655440000",
                    "inbound_order_created",
                    {
                        "location_id": 1,
                        "country": "CO",
                        "product_id": 4,
                        "employee_name": "Lucia",
                    },
                ),
                _event(
                    "550e8400-e29b-41d4-a716-446655440001",
                    "auth_login_failed",
                    {"failure_code": "invalid_credentials"},
                    userId=None,
                    sessionId="none",
                ),
                {"event_type": "inbound_order_created"},
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"received": 3, "stored": 2, "rejected": 1}
    assert telemetry_endpoint().endswith("/telemetry/events")
    inbound = saved[0]
    assert inbound["service"] == "backoffice"
    assert inbound["event_type"] == "inbound_order_created"
    assert inbound["tags"] == {
        "location_id": 1,
        "country": "CO",
        "product_id": 4,
    }
    assert "employee_name" not in inbound["tags"]
    assert saved[1]["tags"] == {"failure_code": "invalid_credentials"}
    assert saved[1]["user_id"] is None


def test_tags_keep_only_plan_allowlist():
    tags = tags_for(
        "stock_waste_registered",
        {
            "location_id": 2,
            "reason": "expired",
            "supplier_name": "typed name",
        },
    )
    assert tags == {"location_id": 2, "reason": "expired"}
