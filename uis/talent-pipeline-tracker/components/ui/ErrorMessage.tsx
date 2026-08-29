interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
  homeHref?: string;
}

export function ErrorMessage({
  message,
  onRetry,
  homeHref = "/",
}: ErrorMessageProps) {
  return (
    <div
      className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
      role="alert"
    >
      <p className="font-medium">Something went wrong</p>
      <p className="mt-1">{message}</p>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        {onRetry ? (
          <button
            type="button"
            onClick={onRetry}
            className="rounded-md bg-red-100 px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-200"
          >
            Try again
          </button>
        ) : null}
        <a href={homeHref} className="text-sm font-medium text-red-800 underline">
          Back to home
        </a>
        <a
          href="mailto:hello@brasaland.com"
          className="text-sm font-medium text-red-800 underline"
        >
          Contact support
        </a>
      </div>
    </div>
  );
}
