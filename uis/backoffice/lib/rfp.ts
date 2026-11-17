import { authFetch } from "@repo/auth";

export type RfpSection = {
  department_id: string;
  contact_name: string;
  key_aspects: string[];
  open_questions: string[];
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
