import {
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from "../../../src/data/sampleOperations";
import type { Location, MenuItem, SaleTransaction, TopSellingItem, WasteRecord } from "../../../src/types/models";
import {
  calculateAverageTicket,
  calculateCountryComparison,
  calculateLocationMargin,
  calculateWasteCost,
  findTopSellingItems,
  rankLocationsByPerformance,
} from "../../../src/utils/transformations";

export type OperationsLocationRow = {
  location: Location;
  score: number;
  margin: number;
};

export type OperationsSnapshot = {
  averageTicket: number;
  wasteCost: number;
  totalRevenue: number;
  saleCount: number;
  locations: OperationsLocationRow[];
  topItems: TopSellingItem[];
};

export function getOperationsSnapshot(
  sales: SaleTransaction[] = sampleSales,
  locations: Location[] = sampleLocations,
  menuItems: MenuItem[] = sampleMenuItems,
  wasteRecords: WasteRecord[] = sampleWasteRecords,
): OperationsSnapshot {
  const averageTicket = calculateAverageTicket(sales, "USD");
  const wasteCost = locations.reduce(
    (total, location) =>
      total + calculateWasteCost(wasteRecords, location.id, "USD"),
    0,
  );
  const comparison = calculateCountryComparison(sales, locations, menuItems);
  const ranking = rankLocationsByPerformance(
    locations,
    sales,
    wasteRecords,
    menuItems,
  );
  const topItems = findTopSellingItems(sales, menuItems, 3);
  const totalRevenue =
    comparison.Colombia.totalRevenue.USD + comparison.USA.totalRevenue.USD;

  return {
    averageTicket,
    wasteCost,
    totalRevenue,
    saleCount: sales.length,
    locations: ranking.map(({ location, score }) => ({
      location,
      score,
      margin: calculateLocationMargin(sales, menuItems, location.id, "USD"),
    })),
    topItems,
  };
}
