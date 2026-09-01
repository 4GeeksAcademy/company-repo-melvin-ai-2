import {
  fieldErrorsFromApi,
  getBrasalandApiBase,
  messageForHttpStatus,
  parseApiError,
} from "./client";

describe("parseApiError", () => {
  test("uses a human detail string", () => {
    expect(
      parseApiError(
        { detail: "Incorrect email or password" },
        "Could not log in.",
      ),
    ).toBe("Incorrect email or password");
  });

  test("joins validation msg fields and replaces traceback-like detail", () => {
    expect(
      parseApiError(
        {
          detail: [
            { msg: "email must be a valid address" },
            { msg: "ensure this value has at least 8 characters" },
          ],
        },
        "Could not register.",
      ),
    ).toBe(
      "email must be a valid address; ensure this value has at least 8 characters",
    );
    expect(
      parseApiError(
        { detail: "Traceback (most recent call last): hidden" },
        "Could not log in.",
      ),
    ).toBe("Could not log in.");
    // Technical payloads must never be shown to a Brasaland operator.
    expect(parseApiError(null, "Could not log in.")).toBe("Could not log in.");
  });
});

describe("messageForHttpStatus", () => {
  test("maps 401, 403, 404, and 5xx to Brasaland copy", () => {
    expect(messageForHttpStatus(401, "fallback")).toBe("Please sign in again.");
    expect(messageForHttpStatus(403, "fallback")).toBe(
      "You do not have permission to do that.",
    );
    expect(messageForHttpStatus(404, "fallback")).toBe(
      "We could not find that information.",
    );
    expect(messageForHttpStatus(500, "fallback")).toBe(
      "The Brasaland service had a problem. Try again or contact hello@brasaland.com.",
    );
  });

  test("keeps the fallback for an unknown 4xx", () => {
    // 418 is not a mapped auth decision; leave the caller's copy intact.
    expect(messageForHttpStatus(418, "Could not save.")).toBe("Could not save.");
  });
});

describe("fieldErrorsFromApi", () => {
  test("maps loc and msg onto field names", () => {
    expect(
      fieldErrorsFromApi({
        detail: [
          { loc: ["body", "email"], msg: "email must be a valid address" },
          { loc: ["body", "password"], msg: "ensure this value has at least 8 characters" },
        ],
      }),
    ).toEqual({
      email: "email must be a valid address",
      password: "ensure this value has at least 8 characters",
    });
  });

  test("returns no fields for a non-array payload", () => {
    expect(fieldErrorsFromApi({ detail: "Incorrect email or password" })).toEqual(
      {},
    );
    expect(fieldErrorsFromApi(null)).toEqual({});
  });
});

describe("getBrasalandApiBase", () => {
  const original = process.env.NEXT_PUBLIC_API_BASE_URL;

  afterEach(() => {
    if (original === undefined) {
      delete process.env.NEXT_PUBLIC_API_BASE_URL;
    } else {
      process.env.NEXT_PUBLIC_API_BASE_URL = original;
    }
  });

  test("strips a trailing slash from the env base URL", () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000/";
    expect(getBrasalandApiBase()).toBe("http://localhost:8000");
  });

  test("defaults to localhost:8000 when unset", () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    expect(getBrasalandApiBase()).toBe("http://localhost:8000");
  });
});
