import { clearToken, getToken } from "./token";

export function getBrasalandApiBase(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    "http://localhost:8000"
  );
}

export function parseApiError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return JSON.stringify(item);
      })
      .join("; ");
  }
  return fallback;
}

export function fieldErrorsFromApi(payload: unknown): Record<string, string> {
  if (!payload || typeof payload !== "object") return {};
  const detail = (payload as { detail?: unknown }).detail;
  if (!Array.isArray(detail)) return {};
  const fields: Record<string, string> = {};
  for (const item of detail) {
    if (!item || typeof item !== "object") continue;
    const loc = (item as { loc?: unknown }).loc;
    const msg = (item as { msg?: unknown }).msg;
    if (!Array.isArray(loc) || typeof msg !== "string") continue;
    const name = loc.filter((part) => part !== "body").pop();
    if (typeof name === "string") fields[name] = msg;
  }
  return fields;
}

export class AuthSessionError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "AuthSessionError";
    this.status = status;
  }
}

export async function authFetch(
  path: string,
  options: RequestInit = {},
): Promise<Response> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${getBrasalandApiBase()}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    clearToken();
    if (typeof window !== "undefined") {
      window.location.assign("/login");
    }
    throw new AuthSessionError("Session expired. Please log in again.", 401);
  }

  return response;
}
