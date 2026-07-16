import type { CandidateStage } from "@/types/candidate";
import { formatStage } from "@/lib/labels";

const STAGE_STYLES: Record<CandidateStage, string> = {
  pending: "bg-stone-100 text-stone-700",
  review: "bg-purple-100 text-purple-800",
  personal_interview: "bg-indigo-100 text-indigo-800",
  technical_interview: "bg-cyan-100 text-cyan-800",
  offer_presented: "bg-emerald-100 text-emerald-800",
};

interface StageBadgeProps {
  stage: CandidateStage;
}

export function StageBadge({ stage }: StageBadgeProps) {
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${STAGE_STYLES[stage]}`}
    >
      {formatStage(stage)}
    </span>
  );
}
