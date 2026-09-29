"""Envelope for the temporary telemetry stub. Full allowlist checks come later."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TelemetryEvent(BaseModel):
    """Standard envelope from docs/telemetry/telemetry-plan.md."""

    eventId: str
    timestamp: str
    sessionId: str
    userId: str | None = None
    event_type: str
    schemaVersion: str
    requestId: str
    properties: dict[str, Any] = Field(default_factory=dict)


class TelemetryBatch(BaseModel):
    events: list[TelemetryEvent]


class TelemetryIngest(BaseModel):
    """Loose batch. Items are validated one by one inside the handler."""

    events: list[Any]


class TelemetryReceived(BaseModel):
    received: int
    stored: int
    rejected: int
