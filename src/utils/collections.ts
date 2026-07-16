import { Location, MenuCategory, MenuItem, SaleTransaction } from "../types/models";

const getLocalDateValue = (date: Date): number => {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
};

export const filterSalesByLocation = (
  sales: SaleTransaction[],
  locationId: string,
): SaleTransaction[] => {
  return sales.filter((sale) => sale.locationId === locationId);
};

export const filterSalesByDateRange = (
  sales: SaleTransaction[],
  startDate: Date,
  endDate: Date,
): SaleTransaction[] => {
  const startValue = getLocalDateValue(startDate);
  const endValue = getLocalDateValue(endDate);

  return sales.filter((sale) => {
    const saleDateValue = getLocalDateValue(sale.timestamp);
    return saleDateValue >= startValue && saleDateValue <= endValue;
  });
};

export const filterMenuItemsByCategory = (
  items: MenuItem[],
  category: MenuCategory,
): MenuItem[] => {
  return items.filter((item) => item.category === category);
};

export const filterActiveLocations = (locations: Location[]): Location[] => {
  return locations.filter((location) => location.status === "Active");
};

export const sortLocationsByCapacity = (
  locations: Location[],
  order: "asc" | "desc",
): Location[] => {
  const direction = order === "asc" ? 1 : -1;

  return [...locations].sort(
    (left, right) => (left.seatingCapacity - right.seatingCapacity) * direction,
  );
};

export const sortMenuItemsByPrice = (
  items: MenuItem[],
  currency: "USD" | "COP",
  order: "asc" | "desc",
): MenuItem[] => {
  const direction = order === "asc" ? 1 : -1;

  return [...items].sort(
    (left, right) => (left.basePrice[currency] - right.basePrice[currency]) * direction,
  );
};