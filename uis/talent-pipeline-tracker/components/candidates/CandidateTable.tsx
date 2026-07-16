"use client";

import Link from "next/link";
import type { Candidate } from "@/types/candidate";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { StageBadge } from "@/components/ui/StageBadge";

interface CandidateTableProps {
  candidates: Candidate[];
  returnTo: string;
}

export function CandidateTable({ candidates, returnTo }: CandidateTableProps) {
  if (candidates.length === 0) {
    return (
      <div className="rounded-lg border border-stone-200 bg-white px-6 py-12 text-center">
        <p className="text-stone-600">No candidates match your filters.</p>
        <p className="mt-1 text-sm text-stone-400">
          Try adjusting your search or filter criteria.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-stone-200">
        <thead className="bg-stone-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-500">
              Name
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-500">
              Position
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-500">
              Status
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-stone-500">
              Stage
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-stone-100">
          {candidates.map((candidate) => (
            <tr key={candidate.id} className="hover:bg-stone-50">
              <td className="px-4 py-3">
                <Link
                  href={`/candidates/${candidate.id}?returnTo=${returnTo}`}
                  className="font-medium text-stone-900 hover:text-[#c0392b]"
                >
                  {candidate.full_name}
                </Link>
                <p className="text-xs text-stone-400">{candidate.email}</p>
              </td>
              <td className="px-4 py-3 text-sm text-stone-700">
                {candidate.position}
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={candidate.status} />
              </td>
              <td className="px-4 py-3">
                <StageBadge stage={candidate.stage} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
