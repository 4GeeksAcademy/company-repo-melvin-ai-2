import {
  sampleLocations,
  sampleMenuItems,
  sampleSales,
  sampleWasteRecords,
} from "../../../src/data/sampleOperations";
import type { Location, TopSellingItem } from "../../../src/types/models";
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

export function getOperationsSnapshot(): OperationsSnapshot {
  const averageTicket = calculateAverageTicket(sampleSales, "USD");
  const wasteCost = sampleLocations.reduce(
    (total, location) =>
      total + calculateWasteCost(sampleWasteRecords, location.id, "USD"),
    0,
  );
  const comparison = calculateCountryComparison(
    sampleSales,
    sampleLocations,
    sampleMenuItems,
  );
  const ranking = rankLocationsByPerformance(
    sampleLocations,
    sampleSales,
    sampleWasteRecords,
    sampleMenuItems,
  );
  const topItems = findTopSellingItems(sampleSales, sampleMenuItems, 3);
  const totalRevenue =
    comparison.Colombia.totalRevenue.USD + comparison.USA.totalRevenue.USD;

  return {
    averageTicket,
    wasteCost,
    totalRevenue,
    saleCount: sampleSales.length,
    locations: ranking.map(({ location, score }) => ({
      location,
      score,
      margin: calculateLocationMargin(
        sampleSales,
        sampleMenuItems,
        location.id,
        "USD",
      ),
    })),
    topItems,
  };
}
