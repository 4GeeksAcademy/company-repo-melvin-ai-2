import type {
  Candidate,
  CandidateCreateInput,
  CandidatePatchInput,
  Note,
  NotesResponse,
  PaginatedCandidates,
  RecordFilters,
} from "@/types/candidate";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
const CONNECTION_ERROR =
  "Could not reach the candidate service. Check your connection and try again.";
const REQUEST_FALLBACK =
  "Could not complete that request. Try again or contact hello@brasaland.com.";
const TECHNICAL_ERROR =
  /traceback|status code|unexpected token|internal server error|failed \(\d{3}\)/i;

function sanitizeDetail(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return TECHNICAL_ERROR.test(detail) ? fallback : detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          const msg = String((item as { msg: string }).msg);
          return TECHNICAL_ERROR.test(msg) ? "" : msg;
        }
        return "";
      })
      .filter(Boolean);
    return parts.length > 0 ? parts.join("; ") : fallback;
  }
  return fallback;
}

class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function messageForStatus(status: number): string {
  if (status === 401) return "Please sign in again.";
  if (status === 403) return "You do not have permission to do that.";
  if (status === 404) return "We could not find that candidate.";
  if (status >= 500) {
    return "The candidate service had a problem. Try again or contact hello@brasaland.com.";
  }
  return REQUEST_FALLBACK;
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  if (!API_URL) {
    throw new ApiRequestError(
      "The candidate service is not configured. Contact hello@brasaland.com.",
      0,
    );
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });
  } catch {
    throw new ApiRequestError(CONNECTION_ERROR, 0);
  }

  if (!response.ok) {
    const fallback = messageForStatus(response.status);
    let message = fallback;
    try {
      const body = await response.json();
      message = sanitizeDetail(body?.detail, fallback);
    } catch {
      // keep status-mapped message
    }
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiRequestError(
      "The candidate service returned an unexpected response.",
      response.status,
    );
  }
}

function buildQuery(filters: RecordFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set("status", filters.status);
  if (filters.stage) params.set("stage", filters.stage);
  if (filters.search) params.set("search", filters.search);
  if (filters.page) params.set("page", String(filters.page));
  params.set("limit", String(filters.limit ?? 20));
  const query = params.toString();
  return query ? `?${query}` : "";
}

export async function getRecords(
  filters: RecordFilters = {},
): Promise<PaginatedCandidates> {
  return request<PaginatedCandidates>(`/records${buildQuery(filters)}`);
}

export async function getRecord(id: string): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`);
}

export async function createRecord(
  data: CandidateCreateInput,
): Promise<Candidate> {
  return request<Candidate>("/records", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateRecord(
  id: string,
  data: CandidateCreateInput,
): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export async function patchRecord(
  id: string,
  data: CandidatePatchInput,
): Promise<Candidate> {
  return request<Candidate>(`/records/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function getNotes(recordId: string): Promise<NotesResponse> {
  return request<NotesResponse>(`/records/${recordId}/notes`);
}

export async function addNote(
  recordId: string,
  content: string,
): Promise<Note> {
  return request<Note>(`/records/${recordId}/notes`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export async function deleteNote(
  recordId: string,
  noteId: string,
): Promise<void> {
  await request<void>(`/records/${recordId}/notes/${noteId}`, {
    method: "DELETE",
  });
}

export { ApiRequestError };
