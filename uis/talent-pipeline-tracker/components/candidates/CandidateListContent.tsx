"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getRecords } from "@/lib/api";
import { buildReturnTo } from "@/lib/url";
import type {
  Candidate,
  CandidateStage,
  CandidateStatus,
  PaginatedCandidates,
} from "@/types/candidate";
import { CandidateFilters } from "@/components/candidates/CandidateFilters";
import { CandidateTable } from "@/components/candidates/CandidateTable";
import { Pagination } from "@/components/candidates/Pagination";
import { ErrorMessage } from "@/components/ui/ErrorMessage";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

export function CandidateListContent() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<PaginatedCandidates | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const status = searchParams.get("status") as CandidateStatus | null;
  const stage = searchParams.get("stage") as CandidateStage | null;
  const search = searchParams.get("search") ?? "";
  const page = Number(searchParams.get("page") ?? "1");

  const returnTo = buildReturnTo({
    status: status ?? undefined,
    stage: stage ?? undefined,
    search: search || undefined,
    page: page > 1 ? String(page) : undefined,
  });

  const fetchCandidates = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getRecords({
        status: status ?? undefined,
        stage: stage ?? undefined,
        search: search || undefined,
        page,
        limit: 20,
      });
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load candidates");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [status, stage, search, page]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client fetch on param change
    void fetchCandidates();
  }, [fetchCandidates]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-stone-900">Candidates</h1>
        <p className="mt-1 text-sm text-stone-500">
          Review and manage hiring pipeline across all Brasaland locations.
        </p>
      </div>

      <CandidateFilters />

      {loading && <LoadingSpinner message="Loading candidates..." />}

      {!loading && error && (
        <ErrorMessage message={error} onRetry={fetchCandidates} />
      )}

      {!loading && !error && data && (
        <>
          <CandidateTable
            candidates={data.data as Candidate[]}
            returnTo={returnTo}
          />
          <Pagination total={data.total} page={data.page} limit={data.limit} />
        </>
      )}
    </div>
  );
}
