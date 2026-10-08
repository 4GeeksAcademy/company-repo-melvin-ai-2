import { authFetch } from "@repo/auth";
import { countryLabel, locationLabel } from "@/lib/inventoryLookups";

export type LocationWeek = {
  location_id: string;
  country: string;
  total_purchase_cost: number;
  total_waste_cost: number;
  waste_ratio: number;
  stockout_events_count: number;
  price_alert_events_count: number;
  currency: string;
};

export type WeeklyReport = {
  week_start: string | null;
  locations: LocationWeek[];
};

export const REPORT_COLUMNS: Array<{ key: keyof LocationWeek; label: string }> = [
  { key: "location_id", label: "Location" },
  { key: "country", label: "Country" },
  { key: "total_purchase_cost", label: "Purchase Cost per Location" },
  { key: "total_waste_cost", label: "Waste Cost per Location" },
  { key: "waste_ratio", label: "Waste Ratio" },
  { key: "stockout_events_count", label: "Stockout Frequency" },
  { key: "price_alert_events_count", label: "Price Alert Frequency" },
];

export async function loadWeeklyLocationPerformance(
  weekStart?: string,
): Promise<WeeklyReport> {
  const query = weekStart ? `?week_start=${mondayOf(weekStart)}` : "";
  const response = await authFetch(
    `/reporting/weekly-location-performance${query}`,
  );
  if (!response.ok) {
    throw new Error(
      "The weekly location report is unavailable. Try again or contact hello@brasaland.com.",
    );
  }
  return (await response.json()) as WeeklyReport;
}

export function formatReportCell(
  key: keyof LocationWeek,
  row: LocationWeek,
): string {
  if (key === "location_id") return kitchenName(row.location_id);
  if (key === "country") return countryLabel(row.country);
  if (key === "total_purchase_cost" || key === "total_waste_cost") {
    return formatMoney(Number(row[key]), row.currency);
  }
  if (key === "waste_ratio") return formatWasteRatio(Number(row.waste_ratio));
  return String(row[key]);
}

function kitchenName(locationId: string): string {
  const id = Number(locationId);
  if (!Number.isInteger(id)) return locationId;
  return locationLabel(id);
}

function formatMoney(amount: number, currency: string): string {
  const number = amount.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return `${number} ${currency}`;
}

function formatWasteRatio(ratio: number): string {
  if (!Number.isFinite(ratio)) return "0%";
  return `${(ratio * 100).toLocaleString("en-US", {
    maximumFractionDigits: 1,
  })}%`;
}

export function mondayOf(isoDate: string): string {
  const [year, month, day] = isoDate.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  const weekday = date.getUTCDay();
  const offset = weekday === 0 ? 6 : weekday - 1;
  date.setUTCDate(date.getUTCDate() - offset);
  return date.toISOString().slice(0, 10);
}
