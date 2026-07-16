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

class ApiRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body.detail) {
        message = Array.isArray(body.detail)
          ? body.detail.map((d: { msg: string }) => d.msg).join(", ")
          : String(body.detail);
      }
    } catch {
      // use default message
    }
    throw new ApiRequestError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
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
