import { clearToken, getToken } from "./token";

export const CONNECTION_ERROR =
  "Could not reach the Brasaland service. Check your connection and try again.";

const TECHNICAL_ERROR =
  /traceback|status code|unexpected token|internal server error|failed \(\d{3}\)/i;

export function getBrasalandApiBase(): string {
  return (
    process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
    "http://localhost:8000"
  );
}

export function messageForHttpStatus(status: number, fallback: string): string {
  if (status === 401) return "Please sign in again.";
  if (status === 403) return "You do not have permission to do that.";
  if (status === 404) return "We could not find that information.";
  if (status >= 500) {
    return "The Brasaland service had a problem. Try again or contact hello@brasaland.com.";
  }
  return fallback;
}

export function parseApiError(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== "object") return fallback;
  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string" && detail.trim()) {
    return TECHNICAL_ERROR.test(detail) ? fallback : detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: string }).msg);
        }
        return "";
      })
      .filter(Boolean);
    return parts.length > 0 ? parts.join("; ") : fallback;
  }
  return fallback;
}

export async function brasalandFetch(
  url: string,
  options?: RequestInit,
): Promise<Response> {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error(CONNECTION_ERROR);
  }
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

  const response = await brasalandFetch(`${getBrasalandApiBase()}${path}`, {
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
