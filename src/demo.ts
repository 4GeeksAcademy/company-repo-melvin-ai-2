import {
  Location,
  MenuItem,
  SaleTransaction,
  WasteRecord,
} from "./types/models";
import {
  filterActiveLocations,
  filterSalesByDateRange,
  sortLocationsByCapacity,
} from "./utils/collections";
import { binarySearchLocationByCapacity, findMenuItemByName } from "./utils/search";
import {
  calculateAverageTicket,
  calculateCountryComparison,
  calculateDailyRevenue,
  calculateLocationMargin,
  calculateWasteCost,
  countSalesByPaymentMethod,
  findTopSellingItems,
  groupWasteByReason,
  rankLocationsByPerformance,
} from "./utils/transformations";
import { validateLocation, validateMenuItem, validateSaleTransaction } from "./utils/validations";

const sampleMenuItems: MenuItem[] = [
  {
    id: "ITEM-PICANHA-250",
    name: "Picanha 250g",
    category: "Meat",
    basePrice: { USD: 18.5, COP: 74000 },
    ingredientCost: { USD: 7.2, COP: 28800 },
    prepTimeMinutes: 15,
    isAvailableInColombia: true,
    isAvailableInUSA: true,
    allergens: [],
    status: "Active",
  },
  {
    id: "ITEM-FRIES",
    name: "French Fries",
    category: "Side",
    basePrice: { USD: 4.5, COP: 18000 },
    ingredientCost: { USD: 1.2, COP: 4800 },
    prepTimeMinutes: 8,
    isAvailableInColombia: true,
    isAvailableInUSA: true,
    allergens: [],
    status: "Active",
  },
  {
    id: "ITEM-COKE",
    name: "Coca-Cola",
    category: "Beverage",
    basePrice: { USD: 2.5, COP: 10000 },
    ingredientCost: { USD: 0.8, COP: 3200 },
    prepTimeMinutes: 2,
    isAvailableInColombia: true,
    isAvailableInUSA: true,
    allergens: [],
    status: "Active",
  },
];

const sampleLocations: Location[] = [
  {
    id: "LOC-MEDELLIN-01",
    name: "Brasaland Medellin Centro",
    city: "Medellin",
    country: "Colombia",
    openingYear: 2008,
    seatingCapacity: 80,
    staffCount: 12,
    monthlyRentCost: { USD: 1500, COP: 6000000 },
    averageMonthlyUtilities: { USD: 400, COP: 1600000 },
    manager: "Carlos Jimenez",
    status: "Active",
  },
  {
    id: "LOC-MIAMI-01",
    name: "Brasaland Miami Beach",
    city: "Miami",
    country: "USA",
    openingYear: 2018,
    seatingCapacity: 100,
    staffCount: 15,
    monthlyRentCost: { USD: 5500, COP: 22000000 },
    averageMonthlyUtilities: { USD: 800, COP: 3200000 },
    manager: "Jake Morrison",
    status: "Active",
  },
];

const sampleSales: SaleTransaction[] = [
  {
    id: "TXN-2024-15482",
    locationId: "LOC-MEDELLIN-01",
    itemId: "ITEM-PICANHA-250",
    quantity: 2,
    totalPrice: { USD: 37, COP: 148000 },
    paymentMethod: "Credit card",
    timestamp: new Date("2024-03-15T19:30:00"),
    waiterName: "Maria Gonzalez",
  },
  {
    id: "TXN-2024-15483",
    locationId: "LOC-MIAMI-01",
    itemId: "ITEM-FRIES",
    quantity: 3,
    totalPrice: { USD: 13.5, COP: 54000 },
    paymentMethod: "Cash",
    timestamp: new Date("2024-03-15T20:15:00"),
    waiterName: "John Smith",
  },
  {
    id: "TXN-2024-15484",
    locationId: "LOC-MEDELLIN-01",
    itemId: "ITEM-COKE",
    quantity: 4,
    totalPrice: { USD: 10, COP: 40000 },
    paymentMethod: "Digital wallet",
    timestamp: new Date("2024-03-16T12:00:00"),
    waiterName: "Maria Gonzalez",
  },
];

const sampleWasteRecords: WasteRecord[] = [
  {
    id: "WASTE-001",
    locationId: "LOC-MEDELLIN-01",
    itemId: "ITEM-FRIES",
    quantity: 2,
    reason: "Expired",
    cost: { USD: 2.4, COP: 9600 },
    timestamp: new Date("2024-03-15T22:00:00"),
    reportedBy: "Carlos Jimenez",
  },
  {
    id: "WASTE-002",
    locationId: "LOC-MIAMI-01",
    itemId: "ITEM-PICANHA-250",
    quantity: 1,
    reason: "Cooking error",
    cost: { USD: 7.2, COP: 28800 },
    timestamp: new Date("2024-03-16T09:00:00"),
    reportedBy: "Jake Morrison",
  },
];

const sortedLocations = sortLocationsByCapacity(sampleLocations, "asc");

console.log("active locations", filterActiveLocations(sampleLocations).map((location) => location.id));
console.log(
  "sales in range",
  filterSalesByDateRange(
    sampleSales,
    new Date("2024-03-15T00:00:00"),
    new Date("2024-03-15T23:59:59"),
  ).map((sale) => sale.id),
);
console.log("find menu item", findMenuItemByName(sampleMenuItems, "french fries")?.id ?? null);
console.log("capacity search index", binarySearchLocationByCapacity(sortedLocations, 100));
console.log("daily revenue USD", calculateDailyRevenue(sampleSales, new Date("2024-03-15"), "USD"));
console.log(
  "location margin Medellin USD",
  calculateLocationMargin(sampleSales, sampleMenuItems, "LOC-MEDELLIN-01", "USD"),
);
console.log("waste cost Medellin COP", calculateWasteCost(sampleWasteRecords, "LOC-MEDELLIN-01", "COP"));
console.log("payment methods", countSalesByPaymentMethod(sampleSales));
console.log("average ticket USD", calculateAverageTicket(sampleSales, "USD"));
console.log(
  "top selling items",
  findTopSellingItems(sampleSales, sampleMenuItems, 2).map((entry) => ({
    id: entry.item.id,
    totalSold: entry.totalSold,
  })),
);
console.log(
  "waste groups",
  Object.fromEntries(
    Object.entries(groupWasteByReason(sampleWasteRecords)).map(([reason, records]) => [reason, records.length]),
  ),
);
console.log(
  "country comparison",
  calculateCountryComparison(sampleSales, sampleLocations, sampleMenuItems),
);
console.log(
  "location ranking",
  rankLocationsByPerformance(
    sampleLocations,
    sampleSales,
    sampleWasteRecords,
    sampleMenuItems,
  ).map((entry) => ({ id: entry.location.id, score: entry.score })),
);
console.log("validate menu item", validateMenuItem(sampleMenuItems[0]));
console.log("validate sale", validateSaleTransaction(sampleSales[0]));
console.log("validate location", validateLocation(sampleLocations[0]));