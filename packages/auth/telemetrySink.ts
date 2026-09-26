/** Opaque session and operator id for telemetry. No email, name, or password. */

const SESSION_KEY = "brasaland_telemetry_session";
const USER_KEY = "brasaland_telemetry_user";

type AuthTelemetry = (
  eventType: string,
  properties: Record<string, unknown>,
) => void;

let authTelemetry: AuthTelemetry | null = null;

export function setAuthTelemetry(handler: AuthTelemetry | null): void {
  authTelemetry = handler;
}

export function emitAuthTelemetry(
  eventType: string,
  properties: Record<string, unknown>,
): void {
  authTelemetry?.(eventType, properties);
}

export function startTelemetrySession(): string {
  if (typeof window === "undefined") return "none";
  const existing = window.sessionStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = window.crypto.randomUUID();
  window.sessionStorage.setItem(SESSION_KEY, created);
  return created;
}

export function readTelemetrySession(): string {
  if (typeof window === "undefined") return "none";
  return window.sessionStorage.getItem(SESSION_KEY) || "none";
}

export function rememberTelemetryUser(userId: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(USER_KEY, userId);
}

export function readTelemetryUser(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(USER_KEY);
}

export function clearTelemetryUser(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(USER_KEY);
}
