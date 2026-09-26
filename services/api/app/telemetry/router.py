"""Temporary ingest. Validates the envelope and does not store events."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter

from app.telemetry.schemas import TelemetryBatch, TelemetryReceived

logger = logging.getLogger("brasaland.telemetry")

def telemetry_endpoint() -> str:
    """Read on each request so the stub can move to storage without a frontend change."""
    return os.environ.get(
        "TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events"
    )

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.post("/events", response_model=TelemetryReceived)
def receive_events(batch: TelemetryBatch) -> TelemetryReceived:
    count = len(batch.events)
    kinds = [event.event_type for event in batch.events]
    logger.info(
        "telemetry stub received %s events types=%s endpoint=%s",
        count,
        kinds,
        telemetry_endpoint(),
    )
    return TelemetryReceived(received=count)
