import type { CandidateStatus } from "@/types/candidate";
import { formatStatus } from "@/lib/labels";

const STATUS_STYLES: Record<CandidateStatus, string> = {
  received: "bg-blue-100 text-blue-800",
  in_progress: "bg-amber-100 text-amber-800",
  selected: "bg-green-100 text-green-800",
  discarded: "bg-stone-100 text-stone-600",
};

interface StatusBadgeProps {
  status: CandidateStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}
    >
      {formatStatus(status)}
    </span>
  );
}
