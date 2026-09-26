"use client";

import {
  readTelemetrySession,
  readTelemetryUser,
  setAuthTelemetry,
} from "@repo/auth";

const SCHEMA_VERSION = "1.0.0";
const FLUSH_MS = 10_000;
const FLUSH_AT = 20;
const MAX_ATTEMPTS = 3;

type Envelope = {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string | null;
  event_type: string;
  schemaVersion: string;
  requestId: string;
  properties: Record<string, unknown>;
};

type Queued = { event: Envelope; attempts: number };

const queue: Queued[] = [];
let timer: number | null = null;
let flushing = false;
let listening = false;
let errorsInstalled = false;

function endpoint(): string {
  return (
    process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT ||
    "http://localhost:8000/telemetry/events"
  );
}

function envelope(
  eventType: string,
  properties: Record<string, unknown>,
): Envelope {
  return {
    eventId: crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    sessionId: readTelemetrySession(),
    userId: readTelemetryUser(),
    event_type: eventType,
    schemaVersion: SCHEMA_VERSION,
    requestId: crypto.randomUUID(),
    properties,
  };
}

async function postBatch(events: Envelope[], beacon: boolean): Promise<boolean> {
  const body = JSON.stringify({ events });
  const url = endpoint();
  if (beacon && typeof navigator !== "undefined" && navigator.sendBeacon) {
    const blob = new Blob([body], { type: "application/json" });
    if (navigator.sendBeacon(url, blob)) return true;
  }
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function flush(useBeacon = false): Promise<void> {
  if (flushing || queue.length === 0) return;
  flushing = true;
  const batch = queue.splice(0, queue.length);
  const ok = await postBatch(
    batch.map((item) => item.event),
    useBeacon,
  );
  if (!ok) {
    const retryable = batch
      .map((item) => ({ ...item, attempts: item.attempts + 1 }))
      .filter((item) => item.attempts < MAX_ATTEMPTS);
    if (retryable.length > 0) {
      const delay = 500 * 2 ** (retryable[0].attempts - 1);
      queue.unshift(...retryable);
      window.setTimeout(() => {
        void flush(false);
      }, delay);
    }
  }
  flushing = false;
}

function onVisibility(): void {
  if (document.visibilityState === "hidden") {
    void flush(true);
  }
}

function ensureStarted(): void {
  if (typeof window === "undefined" || listening) return;
  listening = true;
  timer = window.setInterval(() => {
    void flush(false);
  }, FLUSH_MS);
  document.addEventListener("visibilitychange", onVisibility);
}

/** Only public sender. Callers pass event_type and allowlisted properties. */
export function track(
  eventType: string,
  properties: Record<string, unknown> = {},
): void {
  if (typeof window === "undefined") return;
  ensureStarted();
  queue.push({ event: envelope(eventType, properties), attempts: 0 });
  if (queue.length >= FLUSH_AT) {
    void flush(false);
  }
}

export function installClientErrorTracking(): void {
  if (typeof window === "undefined" || errorsInstalled) return;
  errorsInstalled = true;
  window.addEventListener("error", (event) => {
    track("client_error_uncaught", {
      error_name: event.error?.name || "Error",
      route: window.location.pathname,
    });
  });
  window.addEventListener("unhandledrejection", () => {
    track("client_error_uncaught", {
      error_name: "UnhandledRejection",
      route: window.location.pathname,
    });
  });
}

setAuthTelemetry((eventType, properties) => {
  track(eventType, properties);
});
