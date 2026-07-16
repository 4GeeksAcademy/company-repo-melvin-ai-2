"use client";

import { useState } from "react";
import type { CandidateStage, CandidateStatus } from "@/types/candidate";
import { STATUS_OPTIONS, STAGE_OPTIONS } from "@/lib/labels";
import { patchRecord } from "@/lib/api";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StageBadge } from "@/components/ui/StageBadge";
import { SuccessMessage } from "@/components/ui/SuccessMessage";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface StatusStageControlsProps {
  candidateId: string;
  status: CandidateStatus;
  stage: CandidateStage;
  onUpdate: (updates: { status?: CandidateStatus; stage?: CandidateStage }) => void;
}

export function StatusStageControls({
  candidateId,
  status,
  stage,
  onUpdate,
}: StatusStageControlsProps) {
  const [updating, setUpdating] = useState<"status" | "stage" | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleStatusChange = async (newStatus: CandidateStatus) => {
    if (newStatus === status) return;
    const previous = status;
    onUpdate({ status: newStatus });
    setUpdating("status");
    setError(null);
    setSuccess(null);
    try {
      await patchRecord(candidateId, { status: newStatus });
      setSuccess("Status updated successfully.");
    } catch (err) {
      onUpdate({ status: previous });
      setError(err instanceof Error ? err.message : "Failed to update status");
    } finally {
      setUpdating(null);
    }
  };

  const handleStageChange = async (newStage: CandidateStage) => {
    if (newStage === stage) return;
    const previous = stage;
    onUpdate({ stage: newStage });
    setUpdating("stage");
    setError(null);
    setSuccess(null);
    try {
      await patchRecord(candidateId, { stage: newStage });
      setSuccess("Stage updated successfully.");
    } catch (err) {
      onUpdate({ stage: previous });
      setError(err instanceof Error ? err.message : "Failed to update stage");
    } finally {
      setUpdating(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="min-w-[200px]">
          <label htmlFor="status-select" className="mb-1 block text-sm font-medium text-stone-700">
            Status
          </label>
          <div className="flex items-center gap-2">
            <StatusBadge status={status} />
            <select
              id="status-select"
              value={status}
              disabled={updating === "status"}
              onChange={(e) => handleStatusChange(e.target.value as CandidateStatus)}
              className="rounded-md border border-stone-300 px-3 py-1.5 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b] disabled:opacity-60"
            >
              {STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="min-w-[220px]">
          <label htmlFor="stage-select" className="mb-1 block text-sm font-medium text-stone-700">
            Stage
          </label>
          <div className="flex items-center gap-2">
            <StageBadge stage={stage} />
            <select
              id="stage-select"
              value={stage}
              disabled={updating === "stage"}
              onChange={(e) => handleStageChange(e.target.value as CandidateStage)}
              className="rounded-md border border-stone-300 px-3 py-1.5 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b] disabled:opacity-60"
            >
              {STAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {success && <SuccessMessage message={success} />}
      {error && <ErrorMessage message={error} />}
    </div>
  );
}
