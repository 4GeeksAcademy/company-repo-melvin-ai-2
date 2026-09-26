"""Stub ingest accepts the envelope and does not require a session."""

from app.telemetry.router import telemetry_endpoint


def test_stub_counts_events_and_reads_endpoint_env(client, monkeypatch):
    monkeypatch.setenv("TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events")
    response = client.post(
        "/telemetry/events",
        json={
            "events": [
                {
                    "eventId": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-09-25T20:00:00Z",
                    "sessionId": "sess-1",
                    "userId": "7",
                    "event_type": "inbound_order_created",
                    "schemaVersion": "1.0.0",
                    "requestId": "req-1",
                    "properties": {"product_id": 1},
                },
                {
                    "eventId": "550e8400-e29b-41d4-a716-446655440001",
                    "timestamp": "2026-09-25T20:00:01Z",
                    "sessionId": "none",
                    "userId": None,
                    "event_type": "auth_login_failed",
                    "schemaVersion": "1.0.0",
                    "requestId": "req-2",
                    "properties": {"failure_code": "invalid_credentials"},
                },
            ]
        },
    )
    assert response.status_code == 200
    assert response.json() == {"received": 2}
    assert telemetry_endpoint().endswith("/telemetry/events")
