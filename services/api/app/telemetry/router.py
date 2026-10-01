"""Persist telemetry batches. The public URL stays /telemetry/events."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError

from app.telemetry.report import ReportWindowError, report_for
from app.telemetry.schemas import TelemetryEvent, TelemetryIngest, TelemetryReceived
from app.telemetry.store import (
    SERVICE_NAME,
    insert_batch,
    parse_timestamp,
    tags_for,
)

logger = logging.getLogger("brasaland.telemetry")


def telemetry_endpoint() -> str:
    """Read on each request so storage can move without a frontend change."""
    return os.environ.get(
        "TELEMETRY_ENDPOINT", "http://localhost:8000/telemetry/events"
    )


router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/report")
def read_report(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """Operational report. Same date pair is served from memory for 60 seconds."""
    try:
        return report_for(start_date, end_date)
    except ReportWindowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/events", response_model=TelemetryReceived)
def receive_events(batch: TelemetryIngest) -> TelemetryReceived:
    received = len(batch.events)
    rows: list[dict] = []
    rejected = 0
    for raw in batch.events:
        if not isinstance(raw, dict):
            rejected += 1
            continue
        try:
            event = TelemetryEvent.model_validate(raw)
            timestamp = parse_timestamp(event.timestamp)
        except (ValidationError, ValueError):
            rejected += 1
            continue
        rows.append(
            {
                "event_id": event.eventId,
                "timestamp": timestamp,
                "session_id": event.sessionId,
                "user_id": event.userId,
                "event_type": event.event_type,
                "service": SERVICE_NAME,
                "request_id": event.requestId,
                "tags": tags_for(event.event_type, event.properties),
            }
        )
    stored = insert_batch(rows)
    rejected += len(rows) - stored
    logger.info(
        "telemetry stored %s rejected %s of %s endpoint=%s",
        stored,
        rejected,
        received,
        telemetry_endpoint(),
    )
    return TelemetryReceived(received=received, stored=stored, rejected=rejected)
