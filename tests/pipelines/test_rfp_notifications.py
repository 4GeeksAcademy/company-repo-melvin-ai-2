"""The RFP stream uses SSE framing and the same JWT as the backoffice."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API = ROOT / "services" / "api"
for path in (ROOT, API):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from app.rfp.notifications import (  # noqa: E402
    hub,
    iter_ticket_events,
    publish_ticket_created,
    set_stream_event_limit,
    ticket_created_frame,
)
from tests.factories import LUCIA_EMAIL, LUCIA_PASSWORD, bearer, create_lucia, issue_token  # noqa: E402

PDF = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


@pytest.fixture
def rfp_client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'rfp.db'}")
    monkeypatch.setattr("app.auth.store.AUTH_DB_PATH", tmp_path / "auth.json")
    monkeypatch.setattr("app.rfp.service.RAW_DIR", tmp_path / "raw")
    import app.inventory.db as inventory_db

    inventory_db._engine = None
    monkeypatch.setattr("main.count_suppliers", lambda: 1)
    monkeypatch.setattr("main.seed_auth_if_empty", lambda: "skipped")
    monkeypatch.setattr("main.init_inventory_db", lambda: "skipped")
    monkeypatch.setattr("main.ensure_telemetry_table", lambda: None)
    monkeypatch.setattr("app.rfp.router._run_later", lambda ticket_id: None)

    class _QuietBroker:
        def connection_or_acquire(self):
            return self

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def ensure_connection(self, max_retries=1):
            return None

    import services.celery_app as celery_app_mod

    monkeypatch.setattr(celery_app_mod, "app", _QuietBroker())
    from main import app

    with TestClient(app) as client:
        yield client
    inventory_db._engine = None


def test_an_idle_stream_sends_a_keepalive_comment():
    async def read() -> tuple[str, str]:
        frames = iter_ticket_events(0.01)
        first = await frames.__anext__()
        second = await frames.__anext__()
        await frames.aclose()
        return first, second

    first, second = asyncio.run(read())
    assert first == ": connected\n\n"
    assert second == ": keep-alive\n\n"


def test_two_dashboards_each_receive_the_same_registration():
    first = hub.subscribe()
    second = hub.subscribe()
    try:
        publish_ticket_created("ticket-shared", "analyzing", "2026-11-23T00:00:00+00:00")
        assert first.get(timeout=1)["ticket_id"] == "ticket-shared"
        assert second.get(timeout=1)["status"] == "analyzing"
    finally:
        hub.unsubscribe(first)
        hub.unsubscribe(second)


def test_a_missing_token_receives_no_events(rfp_client):
    response = rfp_client.get("/rfp/tickets/stream")
    assert response.status_code == 401
    assert "event:" not in response.text


def test_uploading_a_pdf_publishes_the_analyzing_ticket(rfp_client):
    create_lucia()
    token = issue_token(rfp_client, LUCIA_EMAIL, LUCIA_PASSWORD)
    subscriber = hub.subscribe()
    try:
        uploaded = rfp_client.post(
            "/rfp/tickets",
            headers=bearer(token),
            files={"file": ("request.pdf", PDF, "application/pdf")},
        )
        payload = subscriber.get(timeout=2)
    finally:
        hub.unsubscribe(subscriber)

    assert uploaded.status_code == 202
    body = uploaded.json()
    assert payload == {
        "ticket_id": body["ticket_id"],
        "status": "analyzing",
        "created_at": body["created_at"],
    }


def test_registration_is_a_named_sse_event(rfp_client):
    create_lucia()
    token = issue_token(rfp_client, LUCIA_EMAIL, LUCIA_PASSWORD)
    set_stream_event_limit(1)

    def publish_when_listening() -> None:
        deadline = time.time() + 3
        while hub.subscriber_count() < 1 and time.time() < deadline:
            time.sleep(0.01)
        publish_ticket_created("ticket-live", "analyzing", "2026-11-23T00:00:00+00:00")

    threading.Thread(target=publish_when_listening, daemon=True).start()
    try:
        response = rfp_client.get("/rfp/tickets/stream", headers=bearer(token))
    finally:
        set_stream_event_limit(None)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: rfp_ticket_created" in response.text
    data_line = next(line for line in response.text.splitlines() if line.startswith("data:"))
    data = json.loads(data_line.split(":", 1)[1].strip())
    assert data == {
        "ticket_id": "ticket-live",
        "status": "analyzing",
        "created_at": "2026-11-23T00:00:00+00:00",
    }
    assert ticket_created_frame(
        data["ticket_id"],
        data["status"],
        data["created_at"],
    ).startswith("event: rfp_ticket_created\ndata:")
