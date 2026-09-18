const TOKEN_KEY = "brasaland_access_token";
export const SESSION_COOKIE = "brasaland_session";

function writeSessionCookie(present: boolean): void {
  if (typeof document === "undefined") return;
  document.cookie = present
    ? `${SESSION_COOKIE}=1; Path=/; SameSite=Lax`
    : `${SESSION_COOKIE}=; Path=/; Max-Age=0; SameSite=Lax`;
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_KEY, token);
  writeSessionCookie(true);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  writeSessionCookie(false);
}

export function hasToken(): boolean {
  return Boolean(getToken());
}
