"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import {
  CONNECTION_ERROR,
  brasalandFetch,
  getBrasalandApiBase,
  messageForHttpStatus,
  parseApiError,
} from "./client";
import { canPaintProtectedView } from "./sessionPaint";
import { clearToken, getToken, hasToken } from "./token";

export function useProtectedSession(hasSessionCookie = false) {
  const router = useRouter();
  const [ready, setReady] = useState(hasSessionCookie);
  const [checking, setChecking] = useState(!hasSessionCookie);
  const [error, setError] = useState<string | null>(null);

  const verify = useCallback(async () => {
    if (!canPaintProtectedView(hasToken())) {
      router.replace("/login");
      return;
    }

    setError(null);
    setReady(true);
    setChecking(false);

    try {
      const token = getToken();
      const response = await brasalandFetch(`${getBrasalandApiBase()}/auth/me`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (response.status === 401) {
        clearToken();
        setReady(false);
        router.replace("/login");
        return;
      }
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(
          parseApiError(
            payload,
            messageForHttpStatus(
              response.status,
              "Could not confirm your Brasaland session. Try again.",
            ),
          ),
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : CONNECTION_ERROR);
      setReady(false);
    }
  }, [router]);

  useEffect(() => {
    void verify();
  }, [verify]);

  return { ready, checking, error, retry: verify };
}
