"use client";

import Link from "next/link";

const SUPPORT_MAIL = "hello@brasaland.com";

type ErrorBannerProps = {
  message: string;
  onRetry?: () => void;
  homeHref?: string;
  homeLabel?: string;
};

export function ErrorBanner({
  message,
  onRetry,
  homeHref = "/",
  homeLabel = "Back to home",
}: ErrorBannerProps) {
  return (
    <div className="ba-error-banner" role="alert">
      <p className="ba-error">{message}</p>
      <p className="ba-error-actions">
        {onRetry ? (
          <button type="button" className="ba-retry" onClick={onRetry}>
            Try again
          </button>
        ) : null}
        <Link href={homeHref}>{homeLabel}</Link>
        <a href={`mailto:${SUPPORT_MAIL}`}>Contact support</a>
      </p>
    </div>
  );
}
