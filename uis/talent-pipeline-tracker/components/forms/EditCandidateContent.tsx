"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getRecord, updateRecord } from "@/lib/api";
import { BackLink } from "@/components/layout/BackLink";
import {
  CandidateForm,
  emptyFormValues,
  type CandidateFormValues,
} from "@/components/forms/CandidateForm";
import type { Candidate } from "@/types/candidate";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { ErrorMessage } from "@/components/ui/ErrorMessage";

interface EditCandidateContentProps {
  id: string;
}

function toFormValues(candidate: Candidate): CandidateFormValues {
  return {
    full_name: candidate.full_name,
    email: candidate.email,
    phone: candidate.phone,
    position: candidate.position,
    experience_years: String(candidate.experience_years),
    linkedin_url: candidate.linkedin_url ?? "",
    cv_url: candidate.cv_url ?? "",
  };
}

export function EditCandidateContent({ id }: EditCandidateContentProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnTo = searchParams.get("returnTo");
  const detailHref = returnTo
    ? `/candidates/${id}?returnTo=${encodeURIComponent(returnTo)}`
    : `/candidates/${id}`;
  const backHref = returnTo ? decodeURIComponent(returnTo) : `/candidates/${id}`;

  const [initialValues, setInitialValues] = useState<CandidateFormValues | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCandidate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const candidate = await getRecord(id);
      setInitialValues(toFormValues(candidate));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load candidate");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client fetch on mount
    void fetchCandidate();
  }, [fetchCandidate]);

  if (loading) {
    return <LoadingSpinner message="Loading candidate..." />;
  }

  if (error || !initialValues) {
    return (
      <div className="space-y-4">
        <BackLink href={backHref} label="Back" />
        <ErrorMessage message={error ?? "Candidate not found"} onRetry={fetchCandidate} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <BackLink href={detailHref} label="Back to candidate" />
        <h1 className="mt-2 text-2xl font-bold text-stone-900">Edit Candidate</h1>
        <p className="mt-1 text-sm text-stone-500">
          Update candidate information for the Brasaland hiring pipeline.
        </p>
      </div>

      <div className="rounded-lg border border-stone-200 bg-white p-6 shadow-sm">
        <CandidateForm
          key={id}
          initialValues={initialValues ?? emptyFormValues}
          submitLabel="Save changes"
          successMessage="Candidate updated successfully."
          onSubmit={async (data) => {
            await updateRecord(id, data);
          }}
          onSuccess={() => {
            router.push(detailHref);
          }}
        />
      </div>
    </div>
  );
}
