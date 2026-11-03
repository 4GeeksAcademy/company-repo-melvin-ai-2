"use client";

import { FormEvent, useState } from "react";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
} from "@/lib/incidentOptions";
import { createIncident, isAuthRedirect } from "@/lib/managedIncidents";

type FormState = {
  title: string;
  description: string;
  category: string;
  status: string;
  origin: string;
  branch: string;
};

const EMPTY: FormState = {
  title: "",
  description: "",
  category: "",
  status: "open",
  origin: "customer",
  branch: "",
};

const MESSAGES: Record<keyof FormState, string> = {
  title: "Enter a short title.",
  description: "Enter a description.",
  category: "Choose a category from the list.",
  status: "Choose a valid status.",
  origin: "Choose where this report came from.",
  branch: "Choose a branch.",
};

function clientErrors(form: FormState): Partial<Record<keyof FormState, string>> {
  const errors: Partial<Record<keyof FormState, string>> = {};
  (Object.keys(MESSAGES) as (keyof FormState)[]).forEach((key) => {
    if (!form[key].trim()) errors[key] = MESSAGES[key];
  });
  return errors;
}

export function IncidentReportForm() {
  const [form, setForm] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  function setField(key: keyof FormState, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const nextErrors = clientErrors(form);
    setErrors(nextErrors);
    setSaved(null);
    if (Object.keys(nextErrors).length > 0) {
      setBanner("Fill in the highlighted fields before sending.");
      return;
    }
    setSending(true);
    setBanner(null);
    try {
      await createIncident(form);
      setForm(EMPTY);
      setErrors({});
      setSaved("Incident recorded. Felipe's team can see it on the board.");
    } catch (error) {
      if (isAuthRedirect(error)) return;
      const field = error instanceof Error ? (error as Error & { field?: string }).field : undefined;
      const message = error instanceof Error ? error.message : "The incident request did not go through. Try again.";
      if (field && field in MESSAGES) {
        setErrors({ [field]: message });
      }
      setBanner(message);
    } finally {
      setSending(false);
    }
  }

  const branchClass =
    form.origin === "branch" ? "incident-field incident-field--branch" : "incident-field";

  return (
    <form className="incident-form" onSubmit={onSubmit} noValidate>
      <label className="incident-field">
        Title
        <input
          name="title"
          value={form.title}
          onChange={(event) => setField("title", event.target.value)}
          required
        />
        {errors.title ? <span role="alert">{errors.title}</span> : null}
      </label>
      <label className="incident-field">
        Description
        <textarea
          name="description"
          rows={4}
          value={form.description}
          onChange={(event) => setField("description", event.target.value)}
          required
        />
        {errors.description ? <span role="alert">{errors.description}</span> : null}
      </label>
      <label className="incident-field">
        Category
        <select
          name="category"
          value={form.category}
          onChange={(event) => setField("category", event.target.value)}
          required
        >
          <option value="">Choose a category</option>
          {INCIDENT_CATEGORIES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.category ? <span role="alert">{errors.category}</span> : null}
      </label>
      <label className="incident-field">
        Status
        <select
          name="status"
          value={form.status}
          onChange={(event) => setField("status", event.target.value)}
          required
        >
          {INCIDENT_STATUSES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.status ? <span role="alert">{errors.status}</span> : null}
      </label>
      <label className="incident-field">
        Origin
        <select
          name="origin"
          value={form.origin}
          onChange={(event) => setField("origin", event.target.value)}
          required
        >
          {INCIDENT_ORIGINS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.origin ? <span role="alert">{errors.origin}</span> : null}
      </label>
      <label className={branchClass}>
        Branch
        <select
          name="branch"
          value={form.branch}
          onChange={(event) => setField("branch", event.target.value)}
          required
        >
          <option value="">Choose a branch</option>
          {INCIDENT_BRANCHES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {form.origin === "branch" ? (
          <span className="muted">This report is coming from a specific location.</span>
        ) : null}
        {errors.branch ? <span role="alert">{errors.branch}</span> : null}
      </label>
      {banner ? (
        <p className="error" role="alert">
          {banner}
        </p>
      ) : null}
      {saved ? (
        <p className="incident-saved" role="status">
          {saved}
        </p>
      ) : null}
      <button className="button" type="submit" disabled={sending}>
        {sending ? "Sending" : "Record incident"}
      </button>
    </form>
  );
}
