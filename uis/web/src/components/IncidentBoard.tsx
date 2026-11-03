"use client";

import { useEffect, useState } from "react";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  labelFor,
} from "@/lib/incidentOptions";
import {
  type IncidentSummary,
  type ManagedIncident,
  isAuthRedirect,
  listIncidents,
  loadIncidentSummary,
  updateIncidentStatus,
} from "@/lib/managedIncidents";

type Filters = { status: string; origin: string; branch: string };

const EMPTY_FILTERS: Filters = { status: "", origin: "", branch: "" };

function CountList({
  title,
  rows,
}: {
  title: string;
  rows: { label: string; count: number }[];
}) {
  return (
    <div>
      <h3>{title}</h3>
      <ul className="stat-list">
        {rows.map((row) => (
          <li key={row.label}>
            <span>{row.label}</span>
            <span>{row.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SummaryPanel() {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let ignore = false;
    loadIncidentSummary().then(
      (next) => {
        if (ignore) return;
        setSummary(next);
        setError(null);
        setLoading(false);
      },
      (err: unknown) => {
        if (ignore || isAuthRedirect(err)) return;
        setSummary(null);
        setError(
          err instanceof Error
            ? err.message
            : "The summary could not be loaded. Try again.",
        );
        setLoading(false);
      },
    );
    return () => {
      ignore = true;
    };
  }, [attempt]);

  function retry() {
    setLoading(true);
    setError(null);
    setAttempt((value) => value + 1);
  }

  return (
    <section className="panel" aria-labelledby="incident-summary-title">
      <h2 id="incident-summary-title">Summary</h2>
      {loading ? <p>Loading the summary.</p> : null}
      {error ? (
        <p className="error" role="alert">
          {error}{" "}
          <button className="button button--secondary" type="button" onClick={retry}>
            Try again
          </button>
        </p>
      ) : null}
      {summary ? (
        <div className="summary">
          <p>{summary.total} incidents in total.</p>
          <CountList
            title="By status"
            rows={INCIDENT_STATUSES.map((option) => ({
              label: option.label,
              count: summary.by_status[option.value] ?? 0,
            }))}
          />
          <CountList
            title="By category"
            rows={INCIDENT_CATEGORIES.map((option) => ({
              label: option.label,
              count: summary.by_category[option.value] ?? 0,
            }))}
          />
          <CountList
            title="By origin"
            rows={INCIDENT_ORIGINS.map((option) => ({
              label: option.label,
              count: summary.by_origin[option.value] ?? 0,
            }))}
          />
          <CountList
            title="By branch"
            rows={INCIDENT_BRANCHES.map((option) => ({
              label: option.label,
              count: summary.by_branch[option.value] ?? 0,
            }))}
          />
        </div>
      ) : null}
    </section>
  );
}

export function IncidentBoard() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [rows, setRows] = useState<ManagedIncident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let ignore = false;
    listIncidents(filters).then(
      (next) => {
        if (ignore) return;
        setRows(next);
        setError(null);
        setLoading(false);
      },
      (err: unknown) => {
        if (ignore || isAuthRedirect(err)) return;
        setRows([]);
        setError(
          err instanceof Error
            ? err.message
            : "The incident list could not be loaded. Try again.",
        );
        setLoading(false);
      },
    );
    return () => {
      ignore = true;
    };
  }, [filters, attempt]);

  function applyFilter(key: keyof Filters, value: string) {
    setLoading(true);
    setError(null);
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function retry() {
    setLoading(true);
    setError(null);
    setAttempt((value) => value + 1);
  }

  async function onStatus(row: ManagedIncident, status: string) {
    if (status === row.status) return;
    setNotice(null);
    setRows((current) =>
      current.map((item) => (item.id === row.id ? { ...item, status } : item)),
    );
    try {
      const updated = await updateIncidentStatus(row.id, status);
      setRows((current) => current.map((item) => (item.id === row.id ? updated : item)));
    } catch (err) {
      if (isAuthRedirect(err)) return;
      setRows((current) =>
        current.map((item) => (item.id === row.id ? { ...item, status: row.status } : item)),
      );
      setNotice(
        err instanceof Error
          ? err.message
          : "That status change was not saved. The previous status is still in place.",
      );
    }
  }

  return (
    <div className="incident-board">
      <SummaryPanel />
      <section className="panel" aria-labelledby="incident-list-title">
        <h2 id="incident-list-title">Incidents</h2>
        <div className="incident-filters">
          <label>
            Status
            <select
              value={filters.status}
              onChange={(event) => applyFilter("status", event.target.value)}
            >
              <option value="">All statuses</option>
              {INCIDENT_STATUSES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Origin
            <select
              value={filters.origin}
              onChange={(event) => applyFilter("origin", event.target.value)}
            >
              <option value="">All origins</option>
              {INCIDENT_ORIGINS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Branch
            <select
              value={filters.branch}
              onChange={(event) => applyFilter("branch", event.target.value)}
            >
              <option value="">All branches</option>
              {INCIDENT_BRANCHES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {loading ? <p>Loading incidents.</p> : null}
        {error ? (
          <p className="error" role="alert">
            {error}{" "}
            <button className="button button--secondary" type="button" onClick={retry}>
              Try again
            </button>
          </p>
        ) : null}
        {notice ? (
          <p className="error" role="alert">
            {notice}
          </p>
        ) : null}
        {!loading && !error && rows.length === 0 ? (
          <p>No incidents match these filters.</p>
        ) : null}
        {!loading && !error && rows.length > 0 ? (
          <div className="incident-table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Branch</th>
                  <th>Origin</th>
                  <th>Category</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.title}</td>
                    <td>{labelFor(INCIDENT_BRANCHES, row.branch)}</td>
                    <td>{labelFor(INCIDENT_ORIGINS, row.origin)}</td>
                    <td>{labelFor(INCIDENT_CATEGORIES, row.category)}</td>
                    <td>
                      <label className="visually-hidden" htmlFor={`status-${row.id}`}>
                        Status for {row.title}
                      </label>
                      <select
                        id={`status-${row.id}`}
                        value={row.status}
                        onChange={(event) => void onStatus(row, event.target.value)}
                      >
                        {INCIDENT_STATUSES.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
