"""Seed transforms and the incident manager API."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from app.incidents.models import IncidentRecord  # noqa: E402
from app.incidents.service import seed_csv, summary  # noqa: E402
from app.inventory.db import get_inventory_session  # noqa: E402
from packages.shared.incident_validation import seed_record  # noqa: E402
from tests.factories import bearer  # noqa: E402

CSV = REPO / "scripts" / "incidents-brasaland.csv"


def _engine(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'incidents.db'}",
        connect_args={"check_same_thread": False},
    )
    SQLModel.metadata.create_all(engine)
    return engine


def test_seed_matches_briefing_totals(tmp_path):
    engine = _engine(tmp_path)
    with Session(engine) as session:
        inserted, already, notes = seed_csv(session, CSV)
        totals = summary(session)

    assert inserted == 96
    assert already == 0
    assert len(notes) == 4
    assert all(line.startswith("Skipped ") for line in notes)
    assert totals["total"] == 96
    assert totals["by_status"] == {
        "open": 32,
        "in_progress": 0,
        "resolved": 50,
        "discarded": 14,
    }
    assert totals["by_category"]["customer_complaint"] == 48
    assert totals["by_category"]["equipment_failure"] == 17
    assert totals["by_category"]["supply_issue"] == 22
    assert totals["by_category"]["staff_issue"] == 9
    assert totals["by_origin"]["customer"] == 96

    with Session(engine) as session:
        again, already_again, _notes = seed_csv(session, CSV)
        assert again == 0
        assert already_again == 96
        assert summary(session)["total"] == 96


def test_invalid_csv_row_is_not_a_record():
    record, reason = seed_record(
        {
            "incident_id": "BRS-9",
            "date": "2024-01-01",
            "location_id": "",
            "category": "STAFF",
            "description": "short ok text",
            "status": "OPEN",
            "customer_id": "",
            "satisfaction_score": "",
            "reporter_id": "MGR-01",
        }
    )
    assert record is None
    assert reason is not None and "missing_location_id" in reason


def test_api_empty_summary_and_field_errors(tmp_path, client: TestClient, lucia, lucia_token):
    engine = _engine(tmp_path)

    def override_session():
        with Session(engine) as session:
            yield session

    from main import app

    app.dependency_overrides[get_inventory_session] = override_session
    headers = bearer(lucia_token)
    try:
        empty = client.get("/api/incidents/summary", headers=headers)
        assert empty.status_code == 200
        body = empty.json()
        assert body["total"] == 0
        assert body["by_status"]["open"] == 0
        assert body["by_branch"]["central"] == 0

        listed = client.get("/api/incidents", headers=headers)
        assert listed.status_code == 200
        assert listed.json() == []

        missing = client.post(
            "/api/incidents",
            headers=headers,
            json={
                "description": "The fryer stopped heating during service.",
                "category": "equipment_failure",
                "status": "open",
                "origin": "branch",
                "branch": "medellin_centro",
            },
        )
        assert missing.status_code == 400
        assert missing.json()["field"] == "title"
        assert "stack" not in missing.text.lower()

        created = client.post(
            "/api/incidents",
            headers=headers,
            json={
                "title": "Fryer down",
                "description": "The fryer stopped heating during service.",
                "category": "equipment_failure",
                "status": "open",
                "origin": "branch",
                "branch": "medellin_centro",
            },
        )
        assert created.status_code == 201
        incident_id = created.json()["id"]

        illegal = client.patch(
            f"/api/incidents/{incident_id}/status",
            headers=headers,
            json={"status": "resolved"},
        )
        assert illegal.status_code == 400
        assert illegal.json()["field"] == "status"

        moved = client.patch(
            f"/api/incidents/{incident_id}/status",
            headers=headers,
            json={"status": "in_progress"},
        )
        assert moved.status_code == 200
        assert moved.json()["status"] == "in_progress"

        missing_id = client.get("/api/incidents/99999", headers=headers)
        assert missing_id.status_code == 404
    finally:
        app.dependency_overrides.pop(get_inventory_session, None)


def test_model_table_is_registered():
    assert IncidentRecord.__tablename__ == "managed_incidents"
