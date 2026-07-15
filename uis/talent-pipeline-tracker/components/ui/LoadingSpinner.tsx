interface LoadingSpinnerProps {
  message?: string;
}

export function LoadingSpinner({ message = "Loading..." }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16">
      <div
        className="h-8 w-8 animate-spin rounded-full border-4 border-stone-200 border-t-[#c0392b]"
        role="status"
        aria-label="Loading"
      />
      <p className="text-sm text-stone-500">{message}</p>
    </div>
  );
}
