import { AuthSessionError, authFetch, clearToken, getBrasalandApiBase, getToken } from "@repo/auth";

export type RfpEvaluation = {
  overall_pass: boolean;
  feedback_for_generator: string;
  readability: { pass: boolean; score: number | null; details: string };
  relevance: { pass: boolean; missing_aspects: string[] };
  compliance: { pass: boolean; rule_ids: string[]; violations: { rule_id: string; message: string }[] };
};

export type RfpSection = {
  department_id: string;
  contact_name: string;
  key_aspects: string[];
  open_questions: string[];
  draft_content?: string;
  approval_status?: string;
  iterations?: number;
  approver?: string;
  approved_at?: string;
  decision?: string;
  approval_rounds?: number;
  awaiting_decision?: boolean;
  evaluation?: RfpEvaluation | null;
};

export type RfpTicket = {
  ticket_id: string;
  status: string;
  client_name: string;
  location: string;
  service_type: string;
  scope: string;
  deadline: string;
  budget_range: string;
  departments_needed: string[];
  flesch_kincaid: number | null;
  gunning_fog: number | null;
  summary: string;
  open_questions: string[];
  discard_reason: string;
  error_detail: string;
  final_document?: string;
  sections: RfpSection[];
};

export async function uploadRfp(file: File): Promise<RfpTicket> {
  const body = new FormData();
  body.append("file", file);
  const response = await authFetch("/rfp/tickets", { method: "POST", body });
  if (!response.ok) {
    throw new Error(
      "The RFP could not be uploaded. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as RfpTicket;
}

export async function startRfpDraft(ticketId: string): Promise<RfpTicket> {
  const response = await authFetch(`/rfp/tickets/${ticketId}/draft`, { method: "POST" });
  if (!response.ok) {
    throw new Error(
      "The proposal draft could not be started. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as RfpTicket;
}

export async function startRfpApproval(ticketId: string): Promise<RfpTicket> {
  const response = await authFetch(`/rfp/tickets/${ticketId}/approval`, { method: "POST" });
  if (!response.ok) {
    throw new Error(
      "Approval could not be opened. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as RfpTicket;
}

export async function decideRfpSection(
  ticketId: string,
  departmentId: string,
  decision: "approve" | "reject" | "request_changes",
): Promise<RfpTicket> {
  const response = await authFetch(`/rfp/tickets/${ticketId}/approval/${departmentId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision }),
  });
  if (!response.ok) {
    throw new Error(
      "That decision could not be saved. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as RfpTicket;
}

export type RfpTicketNotice = {
  ticket_id: string;
  status: string;
  created_at: string;
};

export function nextBackoffMs(attempt: number): number {
  return Math.min(1000 * 2 ** Math.min(Math.max(attempt, 0), 5), 30_000);
}

export function mergeRfpTickets(current: RfpTicket[], incoming: RfpTicket[]): RfpTicket[] {
  const incomingIds = new Set(incoming.map((ticket) => ticket.ticket_id));
  const onlyLocal = current.filter((ticket) => !incomingIds.has(ticket.ticket_id));
  return [...incoming, ...onlyLocal];
}

export function ticketFromNotice(notice: RfpTicketNotice): RfpTicket {
  return {
    ticket_id: notice.ticket_id,
    status: notice.status,
    client_name: "",
    location: "",
    service_type: "",
    scope: "",
    deadline: "",
    budget_range: "",
    departments_needed: [],
    flesch_kincaid: null,
    gunning_fog: null,
    summary: "",
    open_questions: [],
    discard_reason: "",
    error_detail: "",
    sections: [],
  };
}

export function takeSseEvents(buffer: string): { notices: RfpTicketNotice[]; rest: string } {
  const parts = buffer.split("\n\n");
  const rest = parts.pop() ?? "";
  const notices: RfpTicketNotice[] = [];
  for (const frame of parts) {
    const notice = noticeFromFrame(frame);
    if (notice) notices.push(notice);
  }
  return { notices, rest };
}

function noticeFromFrame(frame: string): RfpTicketNotice | null {
  let eventName = "";
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) eventName = line.slice("event:".length).trim();
    if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trim());
  }
  if (eventName !== "rfp_ticket_created" || dataLines.length === 0) return null;
  try {
    const parsed = JSON.parse(dataLines.join("\n")) as Partial<RfpTicketNotice>;
    if (!parsed.ticket_id || !parsed.status) return null;
    return {
      ticket_id: parsed.ticket_id,
      status: parsed.status,
      created_at: parsed.created_at ?? "",
    };
  } catch {
    return null;
  }
}

export async function readRfpTicketStream(
  onNotice: (notice: RfpTicketNotice) => void,
  signal: AbortSignal,
): Promise<void> {
  const headers = new Headers();
  headers.set("Accept", "text/event-stream");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${getBrasalandApiBase()}/rfp/tickets/stream`, {
    headers,
    signal,
  });
  if (response.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.assign("/login");
    throw new AuthSessionError("Session expired. Please log in again.", 401);
  }
  if (!response.ok || !response.body) {
    throw new Error("The RFP notification stream could not be opened.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) return;
    buffer += decoder.decode(value, { stream: true });
    const parsed = takeSseEvents(buffer);
    buffer = parsed.rest;
    for (const notice of parsed.notices) onNotice(notice);
  }
}

export async function listRfpTickets(): Promise<RfpTicket[]> {
  const response = await authFetch("/rfp/tickets");
  if (!response.ok) {
    throw new Error(
      "The RFP tickets could not be loaded. Try again or contact hello@brasaland.com.",
    );
  }
  const body = (await response.json()) as { tickets: RfpTicket[] };
  return body.tickets;
}

export async function getRfpTicket(ticketId: string): Promise<RfpTicket> {
  const response = await authFetch(`/rfp/tickets/${ticketId}`);
  if (!response.ok) {
    throw new Error(
      "The RFP ticket could not be loaded. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as RfpTicket;
}
