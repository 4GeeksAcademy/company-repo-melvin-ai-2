"""Celery application for Brasaland. The API enqueues. This process does the work.

Redis is the broker and the result backend. ``REDIS_URL`` is the same value
for the API and the worker. The default is the published Docker port so a
worker started on the host can reach a Compose Redis.
"""

from __future__ import annotations

import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

app = Celery("brasaland", broker=REDIS_URL, backend=REDIS_URL)
app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    result_expires=60 * 60 * 24,
)

import services.tasks as _tasks  # noqa: E402,F401
