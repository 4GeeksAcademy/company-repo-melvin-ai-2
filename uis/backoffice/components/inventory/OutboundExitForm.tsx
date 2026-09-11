"use client";

import { useCallback, useEffect, useState } from "react";
import { ErrorBanner } from "@repo/auth";
import {
  createOutbound,
  getIngredient,
  InventoryApiError,
  listIngredients,
  type Ingredient,
} from "@/lib/inventory";
import { BRASALAND_LOCATIONS, formatQuantity } from "@/lib/inventoryLookups";
import { InventoryNav } from "./InventoryNav";

type OutboundExitFormProps = {
  initialIngredientId?: number;
};

export function OutboundExitForm({
  initialIngredientId,
}: OutboundExitFormProps) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [ingredientId, setIngredientId] = useState(
    initialIngredientId ? String(initialIngredientId) : "",
  );
  const [liveIngredient, setLiveIngredient] = useState<Ingredient | null>(null);
  const [quantity, setQuantity] = useState("");
  const [reason, setReason] = useState<"consumption" | "waste">("consumption");
  const [locationId, setLocationId] = useState("1");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [quantityError, setQuantityError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadIngredients = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const rows = await listIngredients();
      setIngredients(rows);
    } catch (err) {
      setIngredients([]);
      setLoadError(
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
    void loadIngredients().catch(() => {
      if (cancelled) return;
    });
    return () => {
      cancelled = true;
    };
  }, [loadIngredients]);

  useEffect(() => {
    const id = Number(ingredientId);
    if (!Number.isInteger(id) || id < 1) {
      return;
    }

    let cancelled = false;
    void getIngredient(id)
      .then((row) => {
        if (!cancelled) setLiveIngredient(row);
      })
      .catch(() => undefined);

    return () => {
      cancelled = true;
    };
  }, [ingredientId]);

  const listed =
    ingredients.find((row) => String(row.id) === ingredientId) ?? null;
  const selected =
    liveIngredient && String(liveIngredient.id) === ingredientId
      ? liveIngredient
      : listed;

  const qty = Number(quantity);
  const overStock =
    selected !== null &&
    Number.isFinite(qty) &&
    qty > 0 &&
    qty > selected.current_stock;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setActionError(null);
    setQuantityError(null);
    setSuccess(null);

    const selectedId = Number(ingredientId);
    if (!Number.isInteger(selectedId) || selectedId < 1) {
      setQuantityError("Choose an ingredient by name.");
      setBusy(false);
      return;
    }
    if (!Number.isFinite(qty) || qty <= 0) {
      setQuantityError("Enter a quantity greater than zero.");
      setBusy(false);
      return;
    }

    try {
      await createOutbound({
        ingredient_id: selectedId,
        quantity: qty,
        reason,
        location_id: Number(locationId),
      });
      const name = selected?.name ?? "ingredient";
      setQuantity("");
      setSuccess(`Logged ${reason} of ${qty} for ${name}.`);
      const refreshed = await getIngredient(selectedId);
      setLiveIngredient(refreshed);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Could not log that exit. Try again.";
      if (err instanceof InventoryApiError && err.status === 400) {
        setQuantityError(message);
      } else {
        setActionError(message);
      }
    } finally {
      setBusy(false);
    }
  }

  const banner = loadError
    ? {
        message: loadError,
        onRetry: () => void loadIngredients().catch(() => undefined),
      }
    : actionError
      ? {
          message: actionError,
          onRetry: () => {
            const formEl = document.querySelector(
              ".inventory-form",
            ) as HTMLFormElement | null;
            formEl?.requestSubmit();
          },
        }
      : null;

  return (
    <div className="supplier-page">
      <div className="welcome">
        <div>
          <p className="kicker">Kitchen inventory</p>
          <h1>Log consumption or waste</h1>
          <p>
            Record an ingredient exit from a Brasaland kitchen. Stock shown here
            is the live chain-wide total; the API rejects any exit that would go
            below zero.
          </p>
        </div>
      </div>
      <InventoryNav />
      {banner ? (
        <ErrorBanner message={banner.message} onRetry={banner.onRetry} />
      ) : null}
      {success ? (
        <p className="inventory-success" role="status">
          {success}
        </p>
      ) : null}
      <section className="supplier-panel" aria-labelledby="outbound-heading">
        <h2 id="outbound-heading">Consumption or waste</h2>
        {loading ? (
          <p role="status">Loading ingredients…</p>
        ) : (
          <form className="supplier-form inventory-form" onSubmit={onSubmit}>
            <label>
              Ingredient
              <select
                required
                value={ingredientId}
                onChange={(event) => setIngredientId(event.target.value)}
              >
                <option value="">Select an ingredient</option>
                {ingredients.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.name}
                  </option>
                ))}
              </select>
            </label>
            <p className="inventory-stock-preview full" aria-live="polite">
              {selected
                ? `Current stock for ${selected.name}: ${formatQuantity(selected.current_stock, selected.unit)}`
                : "Choose an ingredient to see current stock."}
            </p>
            <label>
              Quantity{selected ? ` (${selected.unit})` : ""}
              <input
                type="number"
                min="0.01"
                step="0.01"
                required
                value={quantity}
                aria-invalid={Boolean(quantityError)}
                aria-describedby={
                  quantityError || overStock ? "outbound-quantity-note" : undefined
                }
                onChange={(event) => {
                  setQuantity(event.target.value);
                  setQuantityError(null);
                }}
              />
            </label>
            <div className="full" id="outbound-quantity-note">
              {overStock && selected ? (
                <p className="field-warning" role="status">
                  This quantity is higher than the stock shown for{" "}
                  {selected.name} (
                  {formatQuantity(selected.current_stock, selected.unit)}). You
                  can still submit; the server will reject it if stock is
                  insufficient.
                </p>
              ) : null}
              {quantityError ? (
                <p className="field-error" role="alert">
                  {quantityError}
                </p>
              ) : null}
            </div>
            <label>
              Reason
              <select
                value={reason}
                onChange={(event) =>
                  setReason(event.target.value as "consumption" | "waste")
                }
              >
                <option value="consumption">Consumption</option>
                <option value="waste">Waste</option>
              </select>
            </label>
            <label>
              Kitchen
              <select
                required
                value={locationId}
                onChange={(event) => setLocationId(event.target.value)}
              >
                {BRASALAND_LOCATIONS.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.label}
                  </option>
                ))}
              </select>
            </label>
            <div className="full">
              <button type="submit" disabled={busy || Boolean(loadError)}>
                {busy ? "Saving…" : "Log exit"}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
