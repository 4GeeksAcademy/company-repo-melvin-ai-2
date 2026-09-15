/**
 * @jest-environment node
 */
import { getBrasalandApiBase } from "./client";

describe("getBrasalandApiBase (server)", () => {
  const originalPublic = process.env.NEXT_PUBLIC_API_BASE_URL;
  const originalInternal = process.env.INTERNAL_API_URL;

  afterEach(() => {
    if (originalPublic === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = originalPublic;
    }
    if (originalInternal === undefined) {
      delete process.env.INTERNAL_API_URL;
    } else {
      process.env.INTERNAL_API_URL = originalInternal;
    }
  });

  test("uses INTERNAL_API_URL on the server (Compose service name)", () => {
    process.env.INTERNAL_API_URL = "http://backend:8000/";
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000";
    expect(getBrasalandApiBase()).toBe("http://backend:8000");
  });
});
