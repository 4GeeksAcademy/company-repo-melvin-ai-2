import type { Ingredient } from "@/lib/inventory";
import { track } from "@/lib/telemetry";

/** Operations minimum until a per-product setting exists. Same cutoff as the low badge. */
export const CONFIGURED_MINIMUM_STOCK = 10;

const CATEGORY: Record<string, string> = {
  meat: "protein",
  produce: "vegetable",
  sauce: "sauce",
  beverage: "beverage",
  packaging: "packaging",
  cleaning: "cleaning",
  protein: "protein",
  vegetable: "vegetable",
};

export function productCategory(raw: string): string {
  return CATEGORY[raw] || "packaging";
}

export function telemetryUnit(raw: string): "kg" | "liter" | "unit" {
  if (raw === "kg") return "kg";
  if (raw === "litre" || raw === "liter") return "liter";
  return "unit";
}

export function currencyFor(country: string): "COP" | "USD" {
  return country === "US" ? "USD" : "COP";
}

export function inventoryProperties(
  ingredient: Ingredient,
  locationId: number,
  quantity: number,
): Record<string, unknown> {
  return {
    location_id: locationId,
    country: ingredient.country === "US" ? "US" : "CO",
    product_id: ingredient.id,
    product_category: productCategory(ingredient.category),
    quantity,
    unit: telemetryUnit(ingredient.unit),
    currency: currencyFor(ingredient.country),
  };
}

export function trackDirectStockEditRejected(
  ingredient: Ingredient,
  locationId: number,
  attemptedQuantity: number,
): void {
  track("direct_stock_edit_rejected", {
    ...inventoryProperties(ingredient, locationId, attemptedQuantity),
    rejection_code: "stock_not_directly_writable",
    attempted_field: "current_stock",
  });
}

export function trackStockThreshold(
  ingredient: Ingredient,
  locationId: number,
  orderId: number,
): void {
  if (ingredient.current_stock >= CONFIGURED_MINIMUM_STOCK) return;
  track("stock_threshold_triggered", {
    ...inventoryProperties(ingredient, locationId, ingredient.current_stock),
    threshold_quantity: CONFIGURED_MINIMUM_STOCK,
    triggering_order_id: orderId,
  });
}

const costKey = (productId: number, supplierId: string) =>
  `brasaland_unit_cost:${productId}:${supplierId}`;

export function trackPriceVariance(
  ingredient: Ingredient,
  locationId: number,
  quantity: number,
  supplierId: string,
  unitCost: number,
  orderId: number,
): void {
  const key = costKey(ingredient.id, supplierId);
  const previous = Number(window.sessionStorage.getItem(key));
  window.sessionStorage.setItem(key, String(unitCost));
  if (!Number.isFinite(previous) || previous <= 0) return;
  const ratio = Math.abs(unitCost - previous) / previous;
  if (ratio <= 0.1) return;
  track("ingredient_price_variance_detected", {
    ...inventoryProperties(ingredient, locationId, quantity),
    supplier_id: supplierId,
    baseline_unit_cost: previous,
    observed_unit_cost: unitCost,
    variance_ratio: ratio,
    variance_threshold_ratio: 0.1,
    order_id: orderId,
  });
}
