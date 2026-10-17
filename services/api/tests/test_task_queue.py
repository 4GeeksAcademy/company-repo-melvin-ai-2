"""Queue contract for the weekly pipeline. No Redis and no worker."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.task_status import dead_letter_body, public_result, public_status
from tests.factories import bearer


def test_public_status_uses_the_celery_lifecycle_names():
    assert public_status("PENDING") == "pending"
    assert public_status("STARTED") == "started"
    assert public_status("SUCCESS") == "success"
    assert public_status("FAILURE") == "failure"
    assert public_status("RETRY") == "pending"


def test_result_is_hidden_until_the_task_finishes():
    assert public_result("PENDING", None) is None
    assert public_result("STARTED", None) is None
    assert public_result("SUCCESS", {"run_id": "abc"}) == {"run_id": "abc"}
    assert public_result("FAILURE", RuntimeError("pipeline exited")) == "pipeline exited"


def test_dead_letter_message_is_only_the_failure_record():
    body = dead_letter_body("task-1", 4, "RuntimeError: pipeline exited", "2026-10-17T12:00:00+00:00")
    assert set(body) == {"task_id", "attempt", "error", "timestamp"}
    assert "telemetry_events" not in body["error"]


def test_task_status_requires_a_token_and_reads_redis_state(client, lucia_token, monkeypatch):
    assert client.get("/tasks/task-1").status_code == 401

    class _Queued:
        state = "SUCCESS"
        result = {"run_id": "run-1", "status": "Completed"}

    monkeypatch.setattr("app.tasks.router.AsyncResult", lambda task_id, app: _Queued())
    response = client.get("/tasks/task-1", headers=bearer(lucia_token))
    assert response.status_code == 200
    assert response.json() == {
        "task_id": "task-1",
        "status": "success",
        "result": {"run_id": "run-1", "status": "Completed"},
    }
