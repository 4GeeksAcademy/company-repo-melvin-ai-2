import type {
  CountryMetrics,
  CurrencyCode,
  Location,
  MenuItem,
  PaymentMethod,
  Price,
  RankedLocation,
  SaleTransaction,
  TopSellingItem,
  WasteReason,
  WasteRecord,
} from "../types/models";

const USD_TO_COP_RATE = 4000;
const DAY_MS = 24 * 60 * 60 * 1000;
const round = (value: number): number =>
  Math.round((value + Number.EPSILON) * 100) / 100;
const localDateValue = (date: Date): number =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
const emptyPrice = (): Price => ({ USD: 0, COP: 0 });

export const convertCurrency = (
  amount: number,
  fromCurrency: CurrencyCode,
  toCurrency: CurrencyCode,
): number => {
  if (fromCurrency === toCurrency) return amount;
  return round(
    fromCurrency === "USD"
      ? amount * USD_TO_COP_RATE
      : amount / USD_TO_COP_RATE,
  );
};

export const calculateDailyRevenue = (
  sales: SaleTransaction[],
  date: Date,
  currency: CurrencyCode,
): number =>
  round(
    sales.reduce(
      (total, sale) =>
        localDateValue(sale.timestamp) === localDateValue(date)
          ? total + sale.totalPrice[currency]
          : total,
      0,
    ),
  );

export const calculateLocationMargin = (
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  locationId: string,
  currency: CurrencyCode,
): number => {
  const items = new Map(menuItems.map((item) => [item.id, item]));
  let revenue = 0;
  let ingredientCost = 0;

  for (const sale of sales) {
    if (sale.locationId !== locationId) continue;
    const item = items.get(sale.itemId);
    if (!item) continue;
    revenue += sale.totalPrice[currency];
    ingredientCost += item.ingredientCost[currency] * sale.quantity;
  }

  return revenue > 0 ? round(((revenue - ingredientCost) / revenue) * 100) : 0;
};

export const calculateWasteCost = (
  wasteRecords: WasteRecord[],
  locationId: string,
  currency: CurrencyCode,
): number =>
  round(
    wasteRecords.reduce(
      (total, record) =>
        record.locationId === locationId
          ? total + record.cost[currency]
          : total,
      0,
    ),
  );

export const scoreLocationPerformance = (
  location: Location,
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
): number => {
  const locationSales = sales.filter((sale) => sale.locationId === location.id);
  const revenue = locationSales.reduce(
    (total, sale) => total + sale.totalPrice.USD,
    0,
  );
  const opened = new Date(location.openingYear, 0, 1);
  const operatingDays = Math.max(
    Math.floor((localDateValue(new Date()) - localDateValue(opened)) / DAY_MS) + 1,
    1,
  );
  const revenueScore = Math.min((revenue / operatingDays / 1000) * 40, 40);
  const efficiencyScore = Math.min(
    (locationSales.length / Math.max(location.seatingCapacity, 1)) * 30,
    30,
  );
  const waste = wasteRecords
    .filter((record) => record.locationId === location.id)
    .reduce((total, record) => total + record.cost.USD, 0);
  const wastePercentage = revenue > 0 ? (waste / revenue) * 100 : waste > 0 ? 100 : 0;
  const wasteScore = Math.max(20 - wastePercentage * 2, 0);
  const marginScore = Math.min(
    calculateLocationMargin(sales, menuItems, location.id, "USD") / 10,
    10,
  );

  return round(revenueScore + efficiencyScore + wasteScore + marginScore);
};

export const rankLocationsByPerformance = (
  locations: Location[],
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
): RankedLocation[] =>
  locations
    .map((location) => ({
      location,
      score: scoreLocationPerformance(
        location,
        sales,
        wasteRecords,
        menuItems,
      ),
    }))
    .sort((left, right) => right.score - left.score);

export const countSalesByPaymentMethod = (
  sales: SaleTransaction[],
): Record<PaymentMethod, number> =>
  sales.reduce<Record<PaymentMethod, number>>(
    (counts, sale) => {
      counts[sale.paymentMethod] += 1;
      return counts;
    },
    { Cash: 0, "Credit card": 0, "Debit card": 0, "Digital wallet": 0 },
  );

export const calculateAverageTicket = (
  sales: SaleTransaction[],
  currency: CurrencyCode,
): number =>
  sales.length === 0
    ? 0
    : round(
        sales.reduce((total, sale) => total + sale.totalPrice[currency], 0) /
          sales.length,
      );

export const findTopSellingItems = (
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  topN: number,
): TopSellingItem[] => {
  const totals = new Map<string, number>();
  for (const sale of sales) {
    totals.set(sale.itemId, (totals.get(sale.itemId) ?? 0) + sale.quantity);
  }
  const items = new Map(menuItems.map((item) => [item.id, item]));

  return Array.from(totals.entries())
    .flatMap(([itemId, totalSold]) => {
      const item = items.get(itemId);
      return item ? [{ item, totalSold }] : [];
    })
    .sort((left, right) => right.totalSold - left.totalSold)
    .slice(0, Math.max(topN, 0));
};

export const groupWasteByReason = (
  wasteRecords: WasteRecord[],
): Record<WasteReason, WasteRecord[]> =>
  wasteRecords.reduce<Record<WasteReason, WasteRecord[]>>(
    (groups, record) => {
      groups[record.reason].push(record);
      return groups;
    },
    {
      Expired: [],
      "Cooking error": [],
      "Customer return": [],
      Damage: [],
      Other: [],
    },
  );

export const calculateCountryComparison = (
  sales: SaleTransaction[],
  locations: Location[],
  _menuItems: MenuItem[],
): { Colombia: CountryMetrics; USA: CountryMetrics } => {
  const metrics = {
    Colombia: {
      totalLocations: locations.filter((item) => item.country === "Colombia").length,
      totalRevenue: emptyPrice(),
      averageRevenuePerLocation: emptyPrice(),
      totalSales: 0,
    },
    USA: {
      totalLocations: locations.filter((item) => item.country === "USA").length,
      totalRevenue: emptyPrice(),
      averageRevenuePerLocation: emptyPrice(),
      totalSales: 0,
    },
  };
  const locationsById = new Map(
    locations.map((location) => [location.id, location]),
  );

  for (const sale of sales) {
    const location = locationsById.get(sale.locationId);
    if (!location) continue;
    const country = metrics[location.country];
    country.totalRevenue.USD += sale.totalPrice.USD;
    country.totalRevenue.COP += sale.totalPrice.COP;
    country.totalSales += 1;
  }

  for (const countryName of ["Colombia", "USA"] as const) {
    const country = metrics[countryName];
    if (country.totalLocations > 0) {
      country.averageRevenuePerLocation = {
        USD: round(country.totalRevenue.USD / country.totalLocations),
        COP: round(country.totalRevenue.COP / country.totalLocations),
      };
    }
    country.totalRevenue = {
      USD: round(country.totalRevenue.USD),
      COP: round(country.totalRevenue.COP),
    };
  }

  return metrics;
};
