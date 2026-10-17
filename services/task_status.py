"""Map Celery states to the public task status names."""

from __future__ import annotations

PUBLIC_STATUS = {
    "PENDING": "pending",
    "STARTED": "started",
    "SUCCESS": "success",
    "FAILURE": "failure",
    "RETRY": "pending",
    "REVOKED": "failure",
}


def public_status(state: str) -> str:
    """Return ``pending``, ``started``, ``success``, or ``failure``."""
    return PUBLIC_STATUS.get(state or "", "pending")


def public_result(state: str, value):
    """Return the task value only after it finishes. Pending work has no result."""
    if state == "SUCCESS":
        return value
    if state == "FAILURE":
        return _error_text(value)
    return None


def dead_letter_body(task_id: str, attempt: int, error: str, timestamp: str) -> dict:
    """Lightweight DLQ message. It carries the failure, not the pipeline input."""
    return {
        "task_id": task_id,
        "attempt": attempt,
        "error": error,
        "timestamp": timestamp,
    }


def _error_text(value) -> str:
    if value is None:
        return ""
    message = str(value)
    if "://" in message or "password" in message.lower():
        return "The task failed before it could finish."
    return message[:2000]
