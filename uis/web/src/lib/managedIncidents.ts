import { AuthSessionError, authFetch, parseApiError } from "@repo/auth";

export type ManagedIncident = {
  id: number;
  title: string;
  description: string;
  category: string;
  status: string;
  origin: string;
  branch: string;
  created_at: string;
  updated_at: string;
};

export type IncidentSummary = {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
};

export type FieldProblem = {
  message: string;
  field?: string;
};

const FALLBACK = "The incident request did not go through. Try again or contact hello@brasaland.com.";

async function readProblem(response: Response): Promise<FieldProblem> {
  try {
    const payload = (await response.json()) as { field?: unknown; detail?: unknown };
    const message =
      typeof payload.detail === "string" && payload.detail.trim()
        ? parseApiError(payload, FALLBACK)
        : FALLBACK;
    const field = typeof payload.field === "string" ? payload.field : undefined;
    return { message, field };
  } catch {
    return { message: FALLBACK };
  }
}

export async function createIncident(
  body: Record<string, string>,
): Promise<ManagedIncident> {
  const response = await authFetch("/api/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const problem = await readProblem(response);
    const error = new Error(problem.message) as Error & { field?: string };
    error.field = problem.field;
    throw error;
  }
  return (await response.json()) as ManagedIncident;
}

export async function listIncidents(filters: {
  status?: string;
  origin?: string;
  branch?: string;
}): Promise<ManagedIncident[]> {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.origin) params.set("origin", filters.origin);
  if (filters.branch) params.set("branch", filters.branch);
  const query = params.toString();
  const response = await authFetch(`/api/incidents${query ? `?${query}` : ""}`);
  if (!response.ok) {
    throw new Error((await readProblem(response)).message);
  }
  return (await response.json()) as ManagedIncident[];
}

export async function updateIncidentStatus(
  id: number,
  status: string,
): Promise<ManagedIncident> {
  const response = await authFetch(`/api/incidents/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) {
    throw new Error((await readProblem(response)).message);
  }
  return (await response.json()) as ManagedIncident;
}

export async function loadIncidentSummary(): Promise<IncidentSummary> {
  const response = await authFetch("/api/incidents/summary");
  if (!response.ok) {
    throw new Error((await readProblem(response)).message);
  }
  return (await response.json()) as IncidentSummary;
}

export function isAuthRedirect(error: unknown): boolean {
  return error instanceof AuthSessionError;
}
