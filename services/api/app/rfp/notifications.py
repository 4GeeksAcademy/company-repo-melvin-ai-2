"""One in-process fan-out for a newly registered RFP ticket.

Each open dashboard has its own queue. Publishing walks those queues. A
second API process would not see these subscribers; the upload and the
stream run in the same API process.
"""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from collections.abc import AsyncIterator

EVENT_NAME = "rfp_ticket_created"
KEEPALIVE_SECONDS = 15
_max_events: int | None = None


def set_stream_event_limit(limit: int | None) -> None:
    """Stop a stream after this many ticket frames. Production leaves this unset."""
    global _max_events
    _max_events = limit


class TicketHub:
    """Independent subscriber queues. One registration is copied to each."""

    def __init__(self) -> None:
        self._subscribers: list[queue.Queue] = []
        self._lock = threading.Lock()

    def subscribe(self) -> queue.Queue:
        subscriber: queue.Queue = queue.Queue()
        with self._lock:
            self._subscribers.append(subscriber)
        return subscriber

    def unsubscribe(self, subscriber: queue.Queue) -> None:
        with self._lock:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

    def publish(self, payload: dict) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for subscriber in subscribers:
            subscriber.put(payload)

    def subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)


hub = TicketHub()


def ticket_created_frame(ticket_id: str, status: str, created_at: str) -> str:
    """One SSE frame. The event name is not a generic message type."""
    payload = json.dumps(
        {
            "ticket_id": ticket_id,
            "status": status,
            "created_at": created_at,
        },
        separators=(",", ":"),
    )
    return f"event: {EVENT_NAME}\ndata: {payload}\n\n"


def publish_ticket_created(ticket_id: str, status: str, created_at: str) -> None:
    hub.publish(
        {
            "ticket_id": ticket_id,
            "status": status,
            "created_at": created_at,
        }
    )


async def iter_ticket_events(keepalive_seconds: float = KEEPALIVE_SECONDS) -> AsyncIterator[str]:
    """Yield SSE frames until the client disconnects."""
    subscriber = hub.subscribe()
    emitted = 0
    try:
        yield ": connected\n\n"
        while True:
            try:
                payload = await asyncio.to_thread(subscriber.get, True, keepalive_seconds)
            except queue.Empty:
                yield ": keep-alive\n\n"
                continue
            yield ticket_created_frame(
                str(payload["ticket_id"]),
                str(payload["status"]),
                str(payload["created_at"]),
            )
            emitted += 1
            if _max_events is not None and emitted >= _max_events:
                return
    finally:
        hub.unsubscribe(subscriber)
