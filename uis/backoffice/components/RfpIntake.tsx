"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  decideRfpSection,
  listRfpTickets,
  RfpTicket,
  startRfpApproval,
  startRfpDraft,
  uploadRfp,
} from "@/lib/rfp";

const OWNERS: Record<string, string> = {
  marketing: "Camila Ospina",
  operaciones: "Felipe Guerrero",
  procurement: "Lucía Fernández",
  training: "Jake Morrison",
  ceo: "Mariana Restrepo",
};

export function RfpIntake() {
  const [tickets, setTickets] = useState<RfpTicket[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    const rows = await listRfpTickets();
    setTickets(rows);
    setSelected((current) => current ?? rows[0]?.ticket_id ?? null);
  }

  useEffect(() => {
    let stop = false;
    refresh().catch((err: unknown) => {
      if (stop || (err instanceof Error && err.name === "AuthSessionError")) return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    });
    const timer = window.setInterval(() => {
      refresh().catch(() => undefined);
    }, 2000);
    return () => {
      stop = true;
      window.clearInterval(timer);
    };
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const input = event.currentTarget.elements.namedItem("rfp") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const ticket = await uploadRfp(file);
      setSelected(ticket.ticket_id);
      await refresh();
      event.currentTarget.reset();
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function startDraft(ticketId: string) {
    setError(null);
    try {
      await startRfpDraft(ticketId);
      await refresh();
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    }
  }

  async function startApproval(ticketId: string) {
    setError(null);
    try {
      await startRfpApproval(ticketId);
      await refresh();
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    }
  }

  async function decide(ticketId: string, departmentId: string, decision: "approve" | "reject" | "request_changes") {
    setError(null);
    try {
      await decideRfpSection(ticketId, departmentId, decision);
      await refresh();
    } catch (err) {
      if (err instanceof Error && err.name === "AuthSessionError") return;
      setError(
        err instanceof Error
          ? err.message
          : "Could not reach the Brasaland service. Check your connection and try again.",
      );
    }
  }

  const current = tickets.find((ticket) => ticket.ticket_id === selected) ?? null;

  return (
    <section className="rfp-intake" aria-labelledby="rfp-intake-title">
      <h1 id="rfp-intake-title">RFP intake</h1>
      <p>
        Upload a request for Camila Ospina. After intake, each department drafts
        its section and the ticket shows whether that draft is ready or provisional.
      </p>
      <form onSubmit={onSubmit}>
        <label htmlFor="rfp-file">
          RFP PDF
          <input id="rfp-file" name="rfp" type="file" accept="application/pdf,.pdf" required />
        </label>
        <button type="submit" disabled={uploading}>
          {uploading ? "Saving the PDF" : "Upload"}
        </button>
      </form>
      {error ? (
        <p role="alert">
          {error}{" "}
          <button type="button" onClick={() => void refresh()}>
            Try again
          </button>
        </p>
      ) : null}
      <div className="rfp-layout">
        <ul aria-label="RFP tickets">
          {tickets.length === 0 ? <li>No RFPs uploaded yet.</li> : null}
          {tickets.map((ticket) => (
            <li key={ticket.ticket_id}>
              <button
                type="button"
                aria-current={ticket.ticket_id === selected ? "true" : undefined}
                onClick={() => setSelected(ticket.ticket_id)}
              >
                {ticket.client_name || "Unread PDF"} · {ticket.status}
              </button>
            </li>
          ))}
        </ul>
        {current ? (
          <TicketDetail ticket={current} onDraft={startDraft} onApproval={startApproval} onDecide={decide} />
        ) : null}
      </div>
    </section>
  );
}

function TicketDetail({
  ticket,
  onDraft,
  onApproval,
  onDecide,
}: {
  ticket: RfpTicket;
  onDraft: (ticketId: string) => Promise<void>;
  onApproval: (ticketId: string) => Promise<void>;
  onDecide: (
    ticketId: string,
    departmentId: string,
    decision: "approve" | "reject" | "request_changes",
  ) => Promise<void>;
}) {
  const provisional = ticket.sections.filter(
    (section) => section.approval_status === "needs_human_review",
  );
  return (
    <article aria-live="polite">
      <h2>{ticket.client_name || "RFP ticket"}</h2>
      <p>
        Status: <strong>{ticket.status}</strong>
      </p>
      {ticket.status === "intake_complete" ? (
        <button type="button" onClick={() => void onDraft(ticket.ticket_id)}>
          Draft the proposal
        </button>
      ) : null}
      {(ticket.status === "under_evaluation" || ticket.status === "needs_human_review") ? (
        <button type="button" onClick={() => void onApproval(ticket.ticket_id)}>
          Send for approval
        </button>
      ) : null}
      {ticket.final_document ? (
        <section className="rfp-final" aria-label="Final document">
          <h3>Final document</h3>
          <p>{ticket.final_document}</p>
        </section>
      ) : null}
      {provisional.length > 0 ? (
        <p role="status">
          Provisional draft for{" "}
          {provisional
            .map((section) => section.contact_name || OWNERS[section.department_id])
            .join(", ")}
          . A person still needs to review that section. The last draft is kept.
        </p>
      ) : null}
      {ticket.error_detail ? <p role="alert">{ticket.error_detail}</p> : null}
      {ticket.discard_reason ? <p>{ticket.discard_reason}</p> : null}
      {ticket.summary ? <p>{ticket.summary}</p> : null}
      <dl>
        <div>
          <dt>Location</dt>
          <dd>{ticket.location || "Not stated"}</dd>
        </div>
        <div>
          <dt>Service</dt>
          <dd>{ticket.service_type || "Not stated"}</dd>
        </div>
        <div>
          <dt>Scope</dt>
          <dd>{ticket.scope || "Not stated"}</dd>
        </div>
        <div>
          <dt>Deadline</dt>
          <dd>{ticket.deadline || "Not stated"}</dd>
        </div>
        <div>
          <dt>Budget</dt>
          <dd>{ticket.budget_range || "Not stated"}</dd>
        </div>
        <div>
          <dt>Readability</dt>
          <dd>
            {ticket.flesch_kincaid == null
              ? "Not scored"
              : `Flesch-Kincaid ${ticket.flesch_kincaid}, Gunning Fog ${ticket.gunning_fog}`}
          </dd>
        </div>
      </dl>
      {ticket.sections.map((section) => (
        <section key={section.department_id}>
          <h3>
            {section.department_id} · {section.contact_name || OWNERS[section.department_id]}
          </h3>
          <ul>
            {section.key_aspects.map((aspect) => (
              <li key={aspect}>{aspect}</li>
            ))}
          </ul>
          {section.open_questions.length > 0 ? (
            <p>Still open: {section.open_questions.join(" ")}</p>
          ) : null}
          {section.approval_status === "needs_human_review" ? (
            <p>This draft is provisional.</p>
          ) : null}
          {section.approval_status === "approved" ? <p>{section.approver} approved this section.</p> : null}
          {section.approval_status === "rejected" ? (
            <p>Rejected by {section.approver || section.contact_name}. The final document stays unsent.</p>
          ) : null}
          {section.approval_status === "request_changes" ? (
            <p>The change limit was reached. This section is not approved.</p>
          ) : null}
          {section.awaiting_decision ? (
            <div>
              <button type="button" onClick={() => void onDecide(ticket.ticket_id, section.department_id, "approve")}>
                Approve
              </button>
              <button type="button" onClick={() => void onDecide(ticket.ticket_id, section.department_id, "reject")}>
                Reject
              </button>
              <button
                type="button"
                onClick={() => void onDecide(ticket.ticket_id, section.department_id, "request_changes")}
              >
                Request changes
              </button>
            </div>
          ) : null}
          {section.draft_content ? <p>{section.draft_content}</p> : null}
          {section.evaluation ? (
            <p>
              Readability {section.evaluation.readability.pass ? "passed" : "failed"}. Relevance{" "}
              {section.evaluation.relevance.pass ? "passed" : "failed"}. Compliance{" "}
              {section.evaluation.compliance.pass ? "passed" : "failed"}.
              {section.evaluation.feedback_for_generator
                ? ` ${section.evaluation.feedback_for_generator}`
                : ""}
            </p>
          ) : null}
        </section>
      ))}
    </article>
  );
}
