"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { getRecord, getNotes } from "@/lib/api";
import { formatDate } from "@/lib/labels";
import type { Candidate, Note } from "@/types/candidate";
import { BackLink } from "@/components/layout/BackLink";
import { StatusStageControls } from "@/components/detail/StatusStageControls";
import { NotesSection } from "@/components/notes/NotesSection";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StageBadge } from "@/components/ui/StageBadge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface CandidateDetailContentProps {
  id: string;
}

function DetailField({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium uppercase tracking-wide text-stone-400">
        {label}
      </dt>
      <dd className="mt-1 text-sm text-stone-900">{value}</dd>
    </div>
  );
}

export function CandidateDetailContent({ id }: CandidateDetailContentProps) {
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("returnTo");
  const backHref = returnTo ? decodeURIComponent(returnTo) : "/";

  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [record, notesResponse] = await Promise.all([
        getRecord(id),
        getNotes(id),
      ]);
      setCandidate(record);
      setNotes(notesResponse.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load candidate");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client fetch on mount
    void fetchData();
  }, [fetchData]);

  const handleUpdate = (updates: Partial<Candidate>) => {
    setCandidate((prev) => (prev ? { ...prev, ...updates } : prev));
  };

  if (loading) {
    return <LoadingSpinner message="Loading candidate..." />;
  }

  if (error || !candidate) {
    return (
      <div className="space-y-4">
        <BackLink href={backHref} />
        <ErrorMessage message={error ?? "Candidate not found"} onRetry={fetchData} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-2">
          <BackLink href={backHref} />
          <h1 className="text-2xl font-bold text-stone-900">{candidate.full_name}</h1>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={candidate.status} />
            <StageBadge stage={candidate.stage} />
          </div>
        </div>
        <Link
          href={`/candidates/${id}/edit?returnTo=${encodeURIComponent(backHref)}`}
          className="inline-flex items-center rounded-md border border-stone-300 px-4 py-2 text-sm font-medium text-stone-700 hover:bg-stone-50"
        >
          Edit candidate
        </Link>
      </div>

      <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-stone-900">Pipeline</h2>
        <StatusStageControls
          candidateId={id}
          status={candidate.status}
          stage={candidate.stage}
          onUpdate={handleUpdate}
        />
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold text-stone-900">Candidate Details</h2>
        <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="Email" value={candidate.email} />
          <DetailField label="Phone" value={candidate.phone} />
          <DetailField label="Position" value={candidate.position} />
          <DetailField
            label="LinkedIn"
            value={
              candidate.linkedin_url ? (
                <a
                  href={candidate.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#c0392b] hover:underline"
                >
                  View profile
                </a>
              ) : (
                <span className="text-stone-400">Not provided</span>
              )
            }
          />
          <DetailField
            label="CV"
            value={
              candidate.cv_url ? (
                <a
                  href={candidate.cv_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[#c0392b] hover:underline"
                >
                  View CV
                </a>
              ) : (
                <span className="text-stone-400">Not provided</span>
              )
            }
          />
          <DetailField
            label="Years of experience"
            value={candidate.experience_years}
          />
          <DetailField label="Application date" value={formatDate(candidate.applied_at)} />
          <DetailField label="Last updated" value={formatDate(candidate.updated_at)} />
        </dl>
      </section>

      <section className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <NotesSection candidateId={id} initialNotes={notes} />
      </section>
    </div>
  );
}
