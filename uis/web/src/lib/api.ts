import { authFetch } from "@repo/auth";

export type CountRow = {
  count: number;
  percentage: number;
};

export type CategoryRow = CountRow & { category: string };
export type StatusRow = CountRow & { status: string };

export type ScoreRow = {
  score: number;
  label: string;
  count: number;
};

export type AnalysisSummary = {
  source_file: string;
  totals: {
    total_records: number;
    valid_records: number;
    invalid_records: number;
  };
  invalid_breakdown: {
    missing_location_id: number;
    invalid_or_missing_category: number;
    empty_description: number;
    closed_case_no_score: number;
    missing_reporter_id: number;
    score_out_of_range: number;
  };
  by_category: CategoryRow[];
  by_status: StatusRow[];
  satisfaction: {
    scored_cases: number;
    closed_cases: number;
    average_score: number | null;
    by_score: ScoreRow[];
  };
};

export async function analyzeIncidentsCsv(
  file: File,
): Promise<AnalysisSummary> {
  const body = new FormData();
  body.append("file", file);

  const response = await authFetch(`/api/incidents/analyze`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    let detail = `Upload failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }

  return (await response.json()) as AnalysisSummary;
}

export async function downloadResultsCsv(): Promise<void> {
  const response = await authFetch("/api/incidents/results/export");
  if (!response.ok) {
    let detail = `Download failed (${response.status})`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) detail = payload.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "results.csv";
  link.click();
  URL.revokeObjectURL(url);
}
