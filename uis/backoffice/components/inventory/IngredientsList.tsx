"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "@repo/auth";
import { listIngredients, type Ingredient } from "@/lib/inventory";
import { countryLabel, formatQuantity } from "@/lib/inventoryLookups";
import { stockBand, stockBandLabel } from "@/lib/stockBand";
import { InventoryNav } from "./InventoryNav";

export function IngredientsList() {
  const [rows, setRows] = useState<Ingredient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await listIngredients();
      setRows(next);
    } catch (err) {
      setRows([]);
      setError(
        err instanceof Error
          ? err.message
          : "Could not load ingredients. Try again or contact hello@brasaland.com.",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client fetch on mount
    void loadList().catch(() => {
      if (cancelled) return;
    });
    return () => {
      cancelled = true;
    };
  }, [loadList]);

  return (
    <div className="supplier-page">
      <div className="welcome">
        <div>
          <p className="kicker">Kitchen inventory</p>
          <h1>Ingredients on hand</h1>
          <p>
            Chain-wide stock for every Brasaland SKU. Empty, low, and healthy
            bands are visual only; the API still computes stock from deliveries
            minus consumption and waste.
          </p>
        </div>
      </div>
      <InventoryNav />
      {error ? (
        <ErrorBanner
          message={error}
          onRetry={() => void loadList().catch(() => undefined)}
        />
      ) : null}
      <section className="supplier-panel" aria-labelledby="ingredients-heading">
        <h2 id="ingredients-heading">
          Ingredients {loading || error ? "" : `(${rows.length})`}
        </h2>
        {loading ? (
          <p role="status">Loading ingredients…</p>
        ) : error ? null : rows.length === 0 ? (
          <p>No ingredients are registered yet.</p>
        ) : (
          <div className="supplier-table-wrap">
            <table className="supplier-table">
              <thead>
                <tr>
                  <th scope="col">Ingredient</th>
                  <th scope="col">SKU</th>
                  <th scope="col">Category</th>
                  <th scope="col">Market</th>
                  <th scope="col">Stock</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const band = stockBand(row.current_stock);
                  return (
                    <tr key={row.id}>
                      <th scope="row">
                        {row.name}
                        <div className="tiny muted">{row.unit}</div>
                      </th>
                      <td>
                        <code>{row.sku}</code>
                      </td>
                      <td>{row.category}</td>
                      <td>{countryLabel(row.country)}</td>
                      <td>
                        <span className={`stock-badge stock-badge--${band}`}>
                          {stockBandLabel(band)} ·{" "}
                          {formatQuantity(row.current_stock, row.unit)}
                        </span>
                      </td>
                      <td>
                        <div className="inventory-actions">
                          <Link
                            href={`/backoffice/inventory/orders/inbound?ingredient_id=${row.id}`}
                          >
                            Log delivery
                          </Link>
                          <Link
                            href={`/backoffice/inventory/orders/outbound?ingredient_id=${row.id}`}
                          >
                            Log consumption
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
