import type { CandidateStage, CandidateStatus } from "@/types/candidate";

export const STATUS_OPTIONS: { value: CandidateStatus; label: string }[] = [
  { value: "received", label: "Received" },
  { value: "in_progress", label: "In Progress" },
  { value: "selected", label: "Selected" },
  { value: "discarded", label: "Discarded" },
];

export const STAGE_OPTIONS: { value: CandidateStage; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "review", label: "Review" },
  { value: "personal_interview", label: "Personal Interview" },
  { value: "technical_interview", label: "Technical Interview" },
  { value: "offer_presented", label: "Offer Presented" },
];

const STATUS_LABELS: Record<CandidateStatus, string> = {
  received: "Received",
  in_progress: "In Progress",
  selected: "Selected",
  discarded: "Discarded",
};

const STAGE_LABELS: Record<CandidateStage, string> = {
  pending: "Pending",
  review: "Review",
  personal_interview: "Personal Interview",
  technical_interview: "Technical Interview",
  offer_presented: "Offer Presented",
};

export function formatStatus(status: CandidateStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function formatStage(stage: CandidateStage): string {
  return STAGE_LABELS[stage] ?? stage;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}
