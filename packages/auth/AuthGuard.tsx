"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "./ErrorBanner";
import {
  CONNECTION_ERROR,
  brasalandFetch,
  getBrasalandApiBase,
  messageForHttpStatus,
  parseApiError,
} from "./client";
import { clearToken, getToken, hasToken } from "./token";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const checkSession = useCallback(async () => {
    if (!hasToken()) {
      router.replace("/login");
      return;
    }

    setError(null);
    setReady(false);
    setChecking(true);
    try {
      const token = getToken();
      const response = await brasalandFetch(`${getBrasalandApiBase()}/auth/me`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (response.status === 401) {
        clearToken();
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
      setReady(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : CONNECTION_ERROR);
    } finally {
      setChecking(false);
    }
  }, [router]);

  useEffect(() => {
    void checkSession();
  }, [checkSession]);

  if (checking) {
    return (
      <p role="status" style={{ padding: "1.5rem" }}>
        Checking your Brasaland session…
      </p>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "1.5rem" }}>
        <ErrorBanner message={error} onRetry={() => void checkSession()} />
      </div>
    );
  }

  if (!ready) {
    return (
      <p role="status" style={{ padding: "1.5rem" }}>
        Checking your Brasaland session…
      </p>
    );
  }

  return <>{children}</>;
}
