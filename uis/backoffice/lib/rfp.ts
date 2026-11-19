import { authFetch } from "@repo/auth";

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
