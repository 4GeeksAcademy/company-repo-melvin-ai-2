"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ErrorBanner } from "@repo/auth";
import {
  createInbound,
  getIngredient,
  InventoryApiError,
  listIngredients,
  type Ingredient,
} from "@/lib/inventory";
import {
  BRASALAND_LOCATIONS,
  DELIVERY_SUPPLIERS,
  OTHER_SUPPLIER,
} from "@/lib/inventoryLookups";
import { InventoryNav } from "./InventoryNav";
import {
  inventoryProperties,
  trackPriceVariance,
  trackStockThreshold,
} from "@/lib/inventoryTelemetry";
import { track } from "@/lib/telemetry";

type InboundDeliveryFormProps = {
  initialIngredientId?: number;
};

export function InboundDeliveryForm({
  initialIngredientId,
}: InboundDeliveryFormProps) {
  const [ingredients, setIngredients] = useState<Ingredient[]>([]);
  const [ingredientId, setIngredientId] = useState(
    initialIngredientId ? String(initialIngredientId) : "",
  );
  const [quantity, setQuantity] = useState("");
  const [unitCost, setUnitCost] = useState("");
  const [supplierChoice, setSupplierChoice] = useState<string>(
    DELIVERY_SUPPLIERS[0],
  );
  const [otherSupplier, setOtherSupplier] = useState("");
  const [locationId, setLocationId] = useState("1");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const submitted = useRef(false);
  const draft = useRef({ ingredientId: "", quantity: "" });
  draft.current = { ingredientId, quantity };

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
    return () => {
      if (submitted.current) return;
      const current = draft.current;
      if (!current.ingredientId && !current.quantity) return;
      track("backoffice_flow_abandoned", {
        flow_name: "inbound_delivery",
        last_step: current.ingredientId ? "quantity" : "ingredient",
        route: "/backoffice/inventory/orders/inbound",
      });
    };
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

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setActionError(null);
    setFieldError(null);
    setSuccess(null);

    const selectedId = Number(ingredientId);
    const qty = Number(quantity);
    const supplier_name =
      supplierChoice === OTHER_SUPPLIER
        ? otherSupplier.trim()
        : supplierChoice;

    if (!Number.isInteger(selectedId) || selectedId < 1) {
      setFieldError("Choose an ingredient by name.");
      setBusy(false);
      return;
    }
    if (!Number.isFinite(qty) || qty <= 0) {
      setFieldError("Enter a quantity greater than zero.");
      setBusy(false);
      return;
    }
    if (!supplier_name) {
      setFieldError("Enter the supplier name for this delivery.");
      setBusy(false);
      return;
    }

    const cost = Number(unitCost);
    if (!Number.isFinite(cost) || cost < 0) {
      setFieldError("Enter the unit cost in the kitchen's currency.");
      setBusy(false);
      return;
    }
    const ingredient = ingredients.find((row) => row.id === selectedId);
    if (!ingredient) {
      setFieldError("Choose an ingredient by name.");
      setBusy(false);
      return;
    }
    const siteId = Number(locationId);

    try {
      const created = await createInbound({
        ingredient_id: selectedId,
        quantity: qty,
        supplier_name,
        location_id: siteId,
      });
      submitted.current = true;
      track("inbound_order_created", {
        ...inventoryProperties(ingredient, siteId, qty),
        supplier_id: "unmatched",
        unit_cost: cost,
        order_id: created.id,
      });
      trackPriceVariance(ingredient, siteId, qty, "unmatched", cost, created.id);
      const refreshed = await getIngredient(selectedId);
      trackStockThreshold(refreshed, siteId, created.id);
      const name = ingredient.name;
      setIngredientId("");
      setQuantity("");
      setUnitCost("");
      setSupplierChoice(DELIVERY_SUPPLIERS[0]);
      setOtherSupplier("");
      setLocationId("1");
      setSuccess(`Logged a delivery of ${qty} for ${name}.`);
    } catch (err) {
      if (err instanceof InventoryApiError && (err.status === 400 || err.status === 422)) {
        track("inventory_order_validation_failed", {
          order_kind: "inbound",
          failure_code: err.status === 422 ? "invalid_body" : "insufficient_stock",
          http_status: err.status,
          location_id: siteId,
          product_id: selectedId,
          quantity: qty,
        });
      }
      setActionError(
        err instanceof Error
          ? err.message
          : "Could not log that delivery. Try again.",
      );
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

  const selected = ingredients.find((row) => String(row.id) === ingredientId);

  return (
    <div className="supplier-page">
      <div className="welcome">
        <div>
          <p className="kicker">Kitchen inventory</p>
          <h1>Log a supplier delivery</h1>
          <p>
            Record an ingredient entry when a truck arrives. Choose the SKU by
            name, the supplier, and the Brasaland kitchen that received it.
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
      <section className="supplier-panel" aria-labelledby="inbound-heading">
        <h2 id="inbound-heading">Delivery</h2>
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
            <label>
              Quantity{selected ? ` (${selected.unit})` : ""}
              <input
                type="number"
                min="0.01"
                step="0.01"
                required
                value={quantity}
                onChange={(event) => setQuantity(event.target.value)}
              />
            </label>
            <label>
              Unit cost ({selected?.country === "US" ? "USD" : "COP"})
              <input
                type="number"
                min="0"
                step="0.01"
                required
                value={unitCost}
                onChange={(event) => setUnitCost(event.target.value)}
              />
            </label>
            <label>
              Supplier
              <select
                value={supplierChoice}
                onChange={(event) => setSupplierChoice(event.target.value)}
              >
                {DELIVERY_SUPPLIERS.map((name) => (
                  <option key={name} value={name}>
                    {name}
                  </option>
                ))}
                <option value={OTHER_SUPPLIER}>Other</option>
              </select>
            </label>
            {supplierChoice === OTHER_SUPPLIER ? (
              <label className="full">
                Other supplier name
                <input
                  type="text"
                  value={otherSupplier}
                  onChange={(event) => setOtherSupplier(event.target.value)}
                  autoComplete="organization"
                />
              </label>
            ) : null}
            <label>
              Receiving kitchen
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
            {fieldError ? (
              <p className="field-error full" role="alert">
                {fieldError}
              </p>
            ) : null}
            <div className="full">
              <button type="submit" disabled={busy || Boolean(loadError)}>
                {busy ? "Saving…" : "Log delivery"}
              </button>
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
