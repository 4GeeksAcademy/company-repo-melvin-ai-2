export type StockBand = "empty" | "low" | "healthy";

/**
 * Visual stock bands for the ingredients table (not stored, not API rules).
 * Empty: current_stock === 0. Low: 0 < current_stock < 10 in the ingredient unit.
 * Healthy: current_stock >= 10.
 */
export const STOCK_LOW_BELOW = 10;

export function stockBand(current_stock: number): StockBand {
  if (current_stock <= 0) return "empty";
  if (current_stock < STOCK_LOW_BELOW) return "low";
  return "healthy";
}

export function stockBandLabel(band: StockBand): string {
  if (band === "empty") return "Empty";
  if (band === "low") return "Low";
  return "OK";
}
