import { canPaintProtectedView } from "./sessionPaint";

describe("canPaintProtectedView", () => {
  test("paints the workspace when a session token is already stored", () => {
    expect(canPaintProtectedView(true)).toBe(true);
  });

  test("does not paint the workspace when the operator is signed out", () => {
    expect(canPaintProtectedView(false)).toBe(false);
  });
});
