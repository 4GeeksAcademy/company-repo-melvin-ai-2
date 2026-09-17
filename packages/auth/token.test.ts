import { clearToken, getToken, hasToken, setToken } from "./token";

describe("Brasaland access token storage", () => {
  beforeEach(() => {
    window.localStorage.clear();
    document.cookie = "brasaland_session=; Path=/; Max-Age=0";
  });

  test("stores and reads the session token", () => {
    setToken("lucia-session-token");
    expect(getToken()).toBe("lucia-session-token");
    expect(hasToken()).toBe(true);
    expect(document.cookie).toContain("brasaland_session=1");
  });

  test("clearing or missing token means no session", () => {
    expect(getToken()).toBeNull();
    expect(hasToken()).toBe(false);
    setToken("lucia-session-token");
    clearToken();
    // Logout is localStorage-only; the JWT is not revoked server-side.
    expect(getToken()).toBeNull();
    expect(hasToken()).toBe(false);
    expect(document.cookie).not.toContain("brasaland_session=1");
  });
});
