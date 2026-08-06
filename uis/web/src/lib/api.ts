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

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

export function getApiBase(): string {
  return API_BASE;
}

export async function analyzeIncidentsCsv(
  file: File,
): Promise<AnalysisSummary> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE}/api/incidents/analyze`, {
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

export function exportResultsUrl(): string {
  return `${API_BASE}/api/incidents/results/export`;
}
