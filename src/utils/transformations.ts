import {
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
const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;

const roundToTwoDecimals = (value: number): number => {
  return Math.round((value + Number.EPSILON) * 100) / 100;
};

const getLocalDateValue = (date: Date): number => {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
};

const isSameLocalDate = (left: Date, right: Date): boolean => {
  return getLocalDateValue(left) === getLocalDateValue(right);
};

const getPriceAmount = (price: Price, currency: CurrencyCode): number => {
  return price[currency];
};

const getOperatingDays = (openingYear: number): number => {
  const openedAt = new Date(openingYear, 0, 1);
  const today = new Date();
  const dayDifference = Math.floor((getLocalDateValue(today) - getLocalDateValue(openedAt)) / MILLISECONDS_PER_DAY);

  return Math.max(dayDifference + 1, 1);
};

const buildEmptyPrice = (): Price => ({ USD: 0, COP: 0 });

const addPrices = (left: Price, right: Price): Price => {
  return {
    USD: left.USD + right.USD,
    COP: left.COP + right.COP,
  };
};

const buildPaymentMethodCounts = (): Record<PaymentMethod, number> => ({
  Cash: 0,
  "Credit card": 0,
  "Debit card": 0,
  "Digital wallet": 0,
});

const buildWasteGroups = (): Record<WasteReason, WasteRecord[]> => ({
  Expired: [],
  "Cooking error": [],
  "Customer return": [],
  Damage: [],
  Other: [],
});

export const convertCurrency = (
  amount: number,
  fromCurrency: CurrencyCode,
  toCurrency: CurrencyCode,
): number => {
  if (fromCurrency === toCurrency) {
    return amount;
  }

  const convertedAmount =
    fromCurrency === "USD" ? amount * USD_TO_COP_RATE : amount / USD_TO_COP_RATE;

  return roundToTwoDecimals(convertedAmount);
};

export const calculateDailyRevenue = (
  sales: SaleTransaction[],
  date: Date,
  currency: CurrencyCode,
): number => {
  const totalRevenue = sales.reduce((runningTotal, sale) => {
    return isSameLocalDate(sale.timestamp, date)
      ? runningTotal + getPriceAmount(sale.totalPrice, currency)
      : runningTotal;
  }, 0);

  return roundToTwoDecimals(totalRevenue);
};

export const calculateLocationMargin = (
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  locationId: string,
  currency: CurrencyCode,
): number => {
  const menuItemById = new Map(menuItems.map((item) => [item.id, item]));

  let totalRevenue = 0;
  let totalIngredientCost = 0;

  for (const sale of sales) {
    if (sale.locationId !== locationId) {
      continue;
    }

    const menuItem = menuItemById.get(sale.itemId);

    if (!menuItem) {
      continue;
    }

    totalRevenue += getPriceAmount(sale.totalPrice, currency);
    totalIngredientCost += getPriceAmount(menuItem.ingredientCost, currency) * sale.quantity;
  }

  if (totalRevenue <= 0) {
    return 0;
  }

  const margin = ((totalRevenue - totalIngredientCost) / totalRevenue) * 100;
  return roundToTwoDecimals(margin);
};

export const calculateWasteCost = (
  wasteRecords: WasteRecord[],
  locationId: string,
  currency: CurrencyCode,
): number => {
  const totalWasteCost = wasteRecords.reduce((runningTotal, record) => {
    return record.locationId === locationId
      ? runningTotal + getPriceAmount(record.cost, currency)
      : runningTotal;
  }, 0);

  return roundToTwoDecimals(totalWasteCost);
};

export const scoreLocationPerformance = (
  location: Location,
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
): number => {
  const locationSales = sales.filter((sale) => sale.locationId === location.id);
  const totalRevenueUSD = locationSales.reduce((total, sale) => total + sale.totalPrice.USD, 0);
  const operatingDays = getOperatingDays(location.openingYear);
  const averageDailyRevenueUSD = totalRevenueUSD / operatingDays;
  const revenueScore = Math.min((averageDailyRevenueUSD / 1000) * 40, 40);

  const seatEfficiency = location.seatingCapacity > 0 ? locationSales.length / location.seatingCapacity : 0;
  const efficiencyScore = Math.min(seatEfficiency * 30, 30);

  const totalWasteUSD = wasteRecords
    .filter((record) => record.locationId === location.id)
    .reduce((total, record) => total + record.cost.USD, 0);

  const wastePercentage =
    totalRevenueUSD > 0 ? (totalWasteUSD / totalRevenueUSD) * 100 : totalWasteUSD > 0 ? 100 : 0;
  const wasteControlScore = Math.max(20 - wastePercentage * 2, 0);

  const margin = calculateLocationMargin(sales, menuItems, location.id, "USD");
  const profitMarginScore = Math.min(margin / 10, 10);

  return roundToTwoDecimals(
    revenueScore + efficiencyScore + wasteControlScore + profitMarginScore,
  );
};

export const rankLocationsByPerformance = (
  locations: Location[],
  sales: SaleTransaction[],
  wasteRecords: WasteRecord[],
  menuItems: MenuItem[],
): RankedLocation[] => {
  return locations
    .map((location) => ({
      location,
      score: scoreLocationPerformance(location, sales, wasteRecords, menuItems),
    }))
    .sort((left, right) => right.score - left.score);
};

export const countSalesByPaymentMethod = (
  sales: SaleTransaction[],
): Record<PaymentMethod, number> => {
  return sales.reduce((counts, sale) => {
    counts[sale.paymentMethod] += 1;
    return counts;
  }, buildPaymentMethodCounts());
};

export const calculateAverageTicket = (
  sales: SaleTransaction[],
  currency: CurrencyCode,
): number => {
  if (sales.length === 0) {
    return 0;
  }

  const totalRevenue = sales.reduce((runningTotal, sale) => {
    return runningTotal + getPriceAmount(sale.totalPrice, currency);
  }, 0);

  return roundToTwoDecimals(totalRevenue / sales.length);
};

export const findTopSellingItems = (
  sales: SaleTransaction[],
  menuItems: MenuItem[],
  topN: number,
): TopSellingItem[] => {
  const totalsByItemId = new Map<string, number>();

  for (const sale of sales) {
    const currentTotal = totalsByItemId.get(sale.itemId) ?? 0;
    totalsByItemId.set(sale.itemId, currentTotal + sale.quantity);
  }

  const menuItemById = new Map(menuItems.map((item) => [item.id, item]));

  return Array.from(totalsByItemId.entries())
    .map(([itemId, totalSold]) => {
      const item = menuItemById.get(itemId);
      return item ? { item, totalSold } : null;
    })
    .filter((entry): entry is TopSellingItem => entry !== null)
    .sort((left, right) => right.totalSold - left.totalSold)
    .slice(0, Math.max(topN, 0));
};

export const groupWasteByReason = (
  wasteRecords: WasteRecord[],
): Record<WasteReason, WasteRecord[]> => {
  return wasteRecords.reduce((groups, record) => {
    groups[record.reason].push(record);
    return groups;
  }, buildWasteGroups());
};

export const calculateCountryComparison = (
  sales: SaleTransaction[],
  locations: Location[],
  _menuItems: MenuItem[],
): { Colombia: CountryMetrics; USA: CountryMetrics } => {
  const locationById = new Map(locations.map((location) => [location.id, location]));

  const metrics = {
    Colombia: {
      totalLocations: locations.filter((location) => location.country === "Colombia").length,
      totalRevenue: buildEmptyPrice(),
      averageRevenuePerLocation: buildEmptyPrice(),
      totalSales: 0,
    },
    USA: {
      totalLocations: locations.filter((location) => location.country === "USA").length,
      totalRevenue: buildEmptyPrice(),
      averageRevenuePerLocation: buildEmptyPrice(),
      totalSales: 0,
    },
  } satisfies { Colombia: CountryMetrics; USA: CountryMetrics };

  for (const sale of sales) {
    const location = locationById.get(sale.locationId);

    if (!location) {
      continue;
    }

    const countryMetrics = metrics[location.country];
    countryMetrics.totalRevenue = addPrices(countryMetrics.totalRevenue, sale.totalPrice);
    countryMetrics.totalSales += 1;
  }

  for (const country of ["Colombia", "USA"] as const) {
    const countryMetrics = metrics[country];
    const divisor = countryMetrics.totalLocations;

    if (divisor === 0) {
      continue;
    }

    countryMetrics.averageRevenuePerLocation = {
      USD: roundToTwoDecimals(countryMetrics.totalRevenue.USD / divisor),
      COP: roundToTwoDecimals(countryMetrics.totalRevenue.COP / divisor),
    };
  }

  metrics.Colombia.totalRevenue = {
    USD: roundToTwoDecimals(metrics.Colombia.totalRevenue.USD),
    COP: roundToTwoDecimals(metrics.Colombia.totalRevenue.COP),
  };
  metrics.USA.totalRevenue = {
    USD: roundToTwoDecimals(metrics.USA.totalRevenue.USD),
    COP: roundToTwoDecimals(metrics.USA.totalRevenue.COP),
  };

  return metrics;
};