"use client";

import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "@repo/auth";
import {
  VALID_CATEGORIES,
  createSupplier,
  listSuppliers,
  updateSupplierRate,
  updateSupplierStatus,
  type Supplier,
  type SupplierCreateInput,
} from "@/lib/suppliersApi";

const emptyForm: SupplierCreateInput = {
  name: "",
  country: "Colombia",
  categories: ["carne"],
  rate_per_unit: 1,
  currency: "COP",
  status: "active",
  contact_email: "",
  notes: "",
};

function draftsFromRows(rows: Supplier[]): Record<number, string> {
  const drafts: Record<number, string> = {};
  for (const row of rows) {
    drafts[row.id] = String(row.rate_per_unit);
  }
  return drafts;
}

export function SupplierDirectory() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [country, setCountry] = useState("");
  const [category, setCategory] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionRetry, setActionRetry] = useState<(() => void) | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState<SupplierCreateInput>(emptyForm);
  const [rateDrafts, setRateDrafts] = useState<Record<number, string>>({});

  const loadList = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    setActionError(null);
    setActionRetry(null);
    try {
      const rows = await listSuppliers({
        country: country || undefined,
        category: category || undefined,
      });
      setSuppliers(rows);
      setRateDrafts(draftsFromRows(rows));
    } catch (err) {
      setSuppliers([]);
      setRateDrafts({});
      setLoadError(
        err instanceof Error
          ? err.message
          : "Could not load suppliers. Try again or contact hello@brasaland.com.",
      );
      throw err;
    } finally {
      setLoading(false);
    }
  }, [country, category]);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client fetch on filter change
    void loadList().catch(() => {
      if (cancelled) return;
    });
    return () => {
      cancelled = true;
    };
  }, [loadList]);

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setActionError(null);
    setActionRetry(null);
    try {
      const payload: SupplierCreateInput = {
        ...form,
        contact_email: form.contact_email?.trim() || undefined,
        notes: form.notes?.trim() || undefined,
        currency: form.country === "Colombia" ? "COP" : "USD",
      };
      await createSupplier(payload);
      setForm({
        ...emptyForm,
        country: form.country,
        currency: form.country === "Colombia" ? "COP" : "USD",
      });
      await loadList();
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Could not create that supplier. Try again.",
      );
      setActionRetry(() => () => {
        const formEl = document.querySelector(
          ".supplier-form",
        ) as HTMLFormElement | null;
        formEl?.requestSubmit();
      });
    } finally {
      setBusy(false);
    }
  }

  async function onSaveRate(id: number) {
    const raw = rateDrafts[id];
    const value = Number(raw);
    if (!Number.isFinite(value) || value <= 0) {
      setActionError("Rate must be a number greater than 0. Enter a valid rate and try again.");
      setActionRetry(null);
      return;
    }
    setBusy(true);
    setActionError(null);
    setActionRetry(null);
    try {
      await updateSupplierRate(id, value);
      await loadList();
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Could not update that rate. Try again.",
      );
      setActionRetry(() => () => void onSaveRate(id));
    } finally {
      setBusy(false);
    }
  }

  async function onToggleStatus(row: Supplier) {
    const next = row.status === "active" ? "suspended" : "active";
    setBusy(true);
    setActionError(null);
    setActionRetry(null);
    try {
      await updateSupplierStatus(row.id, next);
      await loadList();
    } catch (err) {
      setActionError(
        err instanceof Error
          ? err.message
          : "Could not update that status. Try again.",
      );
      setActionRetry(() => () => void onToggleStatus(row));
    } finally {
      setBusy(false);
    }
  }

  const banner = loadError
    ? { message: loadError, onRetry: () => void loadList().catch(() => undefined) }
    : actionError
      ? { message: actionError, onRetry: actionRetry ?? undefined }
      : null;
  const showTable = !loading && !loadError;
  const emptyList = showTable && suppliers.length === 0;

  return (
    <div className="supplier-page">
      <div className="welcome">
        <div>
          <p className="kicker">Procurement</p>
          <h1>Supplier directory</h1>
          <p>
            Single source of truth for Lucía&apos;s suppliers across Colombia and
            Florida.
          </p>
        </div>
      </div>

      {banner ? (
        <ErrorBanner message={banner.message} onRetry={banner.onRetry} />
      ) : null}

      <section className="supplier-panel" aria-labelledby="filters-heading">
        <h2 id="filters-heading">Filters</h2>
        <div className="supplier-filters">
          <label>
            Country
            <select
              value={country}
              onChange={(event) => setCountry(event.target.value)}
            >
              <option value="">All</option>
              <option value="Colombia">Colombia</option>
              <option value="USA">USA</option>
            </select>
          </label>
          <label>
            Category
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="">All</option>
              {VALID_CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          {loading ? <span className="muted" role="status">Loading…</span> : null}
          {busy && !loading ? <span className="muted">Updating…</span> : null}
        </div>
      </section>

      <section className="supplier-panel" aria-labelledby="list-heading">
        <h2 id="list-heading">
          Suppliers {showTable ? `(${suppliers.length})` : ""}
        </h2>
        {loading ? (
          <p role="status">Loading suppliers…</p>
        ) : emptyList ? (
          <p>No suppliers match these filters.</p>
        ) : showTable ? (
          <div className="supplier-table-wrap">
            <table className="supplier-table">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Country</th>
                  <th scope="col">Categories</th>
                  <th scope="col">Rate</th>
                  <th scope="col">Contact email</th>
                  <th scope="col">Notes</th>
                  <th scope="col">Status</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{row.name}</strong>
                      {row.updated_at ? (
                        <div className="muted tiny">
                          Rate updated {new Date(row.updated_at).toLocaleString()}
                        </div>
                      ) : null}
                    </td>
                    <td>{row.country}</td>
                    <td>{row.categories?.join(", ") || "—"}</td>
                    <td>
                      <div className="rate-edit">
                        <input
                          type="number"
                          step="any"
                          min="0.01"
                          value={rateDrafts[row.id] ?? ""}
                          aria-label={`Rate for ${row.name}`}
                          onChange={(event) =>
                            setRateDrafts((prev) => ({
                              ...prev,
                              [row.id]: event.target.value,
                            }))
                          }
                        />
                        <span>{row.currency}</span>
                        <button
                          type="button"
                          onClick={() => void onSaveRate(row.id)}
                        >
                          Save
                        </button>
                      </div>
                    </td>
                    <td>{row.contact_email || "—"}</td>
                    <td className="notes-cell">{row.notes || "—"}</td>
                    <td>
                      <span className={`status-badge status-badge--${row.status}`}>
                        {row.status}
                      </span>
                    </td>
                    <td>
                      <button type="button" onClick={() => void onToggleStatus(row)}>
                        {row.status === "active" ? "Suspend" : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>

      <section className="supplier-panel" aria-labelledby="register-heading">
        <h2 id="register-heading">Register supplier</h2>
        <form className="supplier-form" onSubmit={onCreate}>
          <label>
            Name
            <input
              required
              value={form.name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, name: event.target.value }))
              }
            />
          </label>
          <label>
            Country
            <select
              value={form.country}
              onChange={(event) => {
                const next = event.target.value as "Colombia" | "USA";
                setForm((prev) => ({
                  ...prev,
                  country: next,
                  currency: next === "Colombia" ? "COP" : "USD",
                }));
              }}
            >
              <option value="Colombia">Colombia</option>
              <option value="USA">USA</option>
            </select>
          </label>
          <label>
            Category
            <select
              value={form.categories[0]}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  categories: [event.target.value],
                }))
              }
            >
              {VALID_CATEGORIES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label>
            Rate per unit
            <input
              required
              type="number"
              step="any"
              min="0.01"
              value={form.rate_per_unit}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  rate_per_unit: Number(event.target.value),
                }))
              }
            />
          </label>
          <label>
            Status
            <select
              value={form.status}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  status: event.target.value as "active" | "suspended",
                }))
              }
            >
              <option value="active">active</option>
              <option value="suspended">suspended</option>
            </select>
          </label>
          <label>
            Contact email
            <input
              type="email"
              value={form.contact_email || ""}
              onChange={(event) =>
                setForm((prev) => ({
                  ...prev,
                  contact_email: event.target.value,
                }))
              }
            />
          </label>
          <label className="full">
            Notes
            <textarea
              value={form.notes || ""}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, notes: event.target.value }))
              }
            />
          </label>
          <button type="submit" disabled={busy || loading}>
            Create supplier
          </button>
        </form>
      </section>
    </div>
  );
}
