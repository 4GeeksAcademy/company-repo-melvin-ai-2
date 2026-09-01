import { clearToken, getToken, hasToken, setToken } from "./token";

describe("Brasaland access token storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  test("stores and reads the session token", () => {
    setToken("lucia-session-token");
    expect(getToken()).toBe("lucia-session-token");
    expect(hasToken()).toBe(true);
  });

  test("clearing or missing token means no session", () => {
    expect(getToken()).toBeNull();
    expect(hasToken()).toBe(false);
    setToken("lucia-session-token");
    clearToken();
    // Logout is localStorage-only; the JWT is not revoked server-side.
    expect(getToken()).toBeNull();
    expect(hasToken()).toBe(false);
  });
});
