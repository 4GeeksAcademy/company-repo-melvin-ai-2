/**
 * A JWT in localStorage is enough to paint the backoffice.
 * GET /auth/me still runs afterwards and can redirect on 401.
 */
export function canPaintProtectedView(hasSessionToken: boolean): boolean {
  return hasSessionToken;
}
