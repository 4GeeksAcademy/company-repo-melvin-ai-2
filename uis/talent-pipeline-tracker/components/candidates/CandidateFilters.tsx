"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useRef } from "react";
import { STATUS_OPTIONS, STAGE_OPTIONS } from "@/lib/labels";
import { buildListQueryString } from "@/lib/url";

export function CandidateFilters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const status = searchParams.get("status") ?? "";
  const stage = searchParams.get("stage") ?? "";
  const searchParam = searchParams.get("search") ?? "";
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updateParams = useCallback(
    (updates: Record<string, string>) => {
      const next = {
        status: "status" in updates ? updates.status : status,
        stage: "stage" in updates ? updates.stage : stage,
        search: "search" in updates ? updates.search : searchParam,
        page: "page" in updates ? updates.page : "",
      };

      if ("status" in updates || "stage" in updates || "search" in updates) {
        next.page = "";
      }

      router.push(`/${buildListQueryString(next)}`);
    },
    [router, status, stage, searchParam],
  );

  const handleSearchChange = (value: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      updateParams({ search: value });
    }, 300);
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
      <div className="min-w-[200px] flex-1">
        <label htmlFor="search" className="mb-1 block text-sm font-medium text-stone-700">
          Search
        </label>
        <input
          id="search"
          key={`search-${searchParam}`}
          type="search"
          placeholder="Search by name or email..."
          defaultValue={searchParam}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b]"
        />
      </div>

      <div className="min-w-[160px]">
        <label htmlFor="status" className="mb-1 block text-sm font-medium text-stone-700">
          Status
        </label>
        <select
          id="status"
          value={status}
          onChange={(e) => updateParams({ status: e.target.value })}
          className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b]"
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="min-w-[180px]">
        <label htmlFor="stage" className="mb-1 block text-sm font-medium text-stone-700">
          Stage
        </label>
        <select
          id="stage"
          value={stage}
          onChange={(e) => updateParams({ stage: e.target.value })}
          className="w-full rounded-md border border-stone-300 px-3 py-2 text-sm focus:border-[#c0392b] focus:outline-none focus:ring-1 focus:ring-[#c0392b]"
        >
          <option value="">All stages</option>
          {STAGE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
