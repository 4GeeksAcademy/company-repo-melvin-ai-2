"use client";

import { ErrorBanner } from "./ErrorBanner";
import { useProtectedSession } from "./useProtectedSession";

export function AuthGuard({
  children,
  hasSessionCookie = false,
}: {
  children: React.ReactNode;
  hasSessionCookie?: boolean;
}) {
  const { ready, checking, error, retry } =
    useProtectedSession(hasSessionCookie);

  if (checking && !ready) {
    return (
      <p role="status" style={{ padding: "1.5rem" }}>
        Checking your Brasaland session…
      </p>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "1.5rem" }}>
        <ErrorBanner message={error} onRetry={() => void retry()} />
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
