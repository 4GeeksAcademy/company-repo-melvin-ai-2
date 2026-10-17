"""Read a queued task without running it."""

from __future__ import annotations

import sys
from pathlib import Path

from celery.result import AsyncResult
from fastapi import APIRouter, Depends

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.auth.deps import get_current_user  # noqa: E402
from services.celery_app import app as celery_app  # noqa: E402
from services.task_status import public_result, public_status  # noqa: E402

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}")
def read_task(task_id: str, _user=Depends(get_current_user)) -> dict:
    """Return the Celery state stored in Redis, plus the result when it exists."""
    queued = AsyncResult(task_id, app=celery_app)
    return {
        "task_id": task_id,
        "status": public_status(queued.state),
        "result": public_result(queued.state, queued.result),
    }
