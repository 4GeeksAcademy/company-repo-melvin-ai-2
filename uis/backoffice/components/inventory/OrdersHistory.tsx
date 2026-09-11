"use client";

import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "@repo/auth";
import { listOrders, type OrderRow } from "@/lib/inventory";
import {
  formatOrderWhen,
  formatQuantity,
  locationLabel,
} from "@/lib/inventoryLookups";
import { InventoryNav } from "./InventoryNav";

function typeLabel(row: OrderRow): string {
  if (row.type === "entry") return "Delivery";
  return row.reason === "waste" ? "Waste" : "Consumption";
}

export function OrdersHistory() {
  const [rows, setRows] = useState<OrderRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const next = await listOrders();
      setRows(next);
    } catch (err) {
      setRows([]);
      setError(
        err instanceof Error
          ? err.message
          : "Could not load orders. Try again or contact hello@brasaland.com.",
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
          <h1>Delivery and exit history</h1>
          <p>
            Read-only list of ingredient deliveries, consumption logs, and waste
            reports. Staff identity is the TinyDB user id stored as{" "}
            <code>user_uuid</code>.
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
      <section className="supplier-panel" aria-labelledby="orders-heading">
        <h2 id="orders-heading">
          Orders {loading || error ? "" : `(${rows.length})`}
        </h2>
        {loading ? (
          <p role="status">Loading orders…</p>
        ) : error ? null : rows.length === 0 ? (
          <p>No deliveries or exits have been logged yet.</p>
        ) : (
          <div className="supplier-table-wrap">
            <table className="supplier-table">
              <thead>
                <tr>
                  <th scope="col">Type</th>
                  <th scope="col">Ingredient</th>
                  <th scope="col">Quantity</th>
                  <th scope="col">Date</th>
                  <th scope="col">user_uuid</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={`${row.type}-${row.id}`}
                    className={
                      row.type === "entry"
                        ? "inventory-row inventory-row--entry"
                        : "inventory-row inventory-row--exit"
                    }
                  >
                    <td>
                      <span
                        className={
                          row.type === "entry"
                            ? "order-type order-type--entry"
                            : row.reason === "waste"
                              ? "order-type order-type--waste"
                              : "order-type order-type--exit"
                        }
                      >
                        {typeLabel(row)}
                      </span>
                      <div className="tiny muted">
                        {row.type === "entry"
                          ? row.supplier_name
                          : locationLabel(row.location_id)}
                      </div>
                    </td>
                    <td>{row.ingredient.name}</td>
                    <td>
                      {formatQuantity(row.quantity, row.ingredient.unit)}
                    </td>
                    <td>{formatOrderWhen(row.created_at)}</td>
                    <td>
                      <code>{row.user_uuid}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
