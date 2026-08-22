import type {
  Location,
  MenuItem,
  Price,
  SaleTransaction,
  ValidationResult,
} from "../types/models";

const hasPositivePrices = (price: Price): boolean =>
  price.USD > 0 && price.COP > 0;
const hasText = (value: string): boolean => value.trim().length > 0;
const result = (errors: string[]): ValidationResult => ({
  valid: errors.length === 0,
  errors,
});

export const validateMenuItem = (item: MenuItem): ValidationResult => {
  const errors: string[] = [];
  if (!hasText(item.name)) errors.push("Menu item name must not be empty.");
  if (!hasPositivePrices(item.basePrice)) {
    errors.push("Menu item basePrice must have USD and COP values greater than 0.");
  }
  if (!hasPositivePrices(item.ingredientCost)) {
    errors.push(
      "Menu item ingredientCost must have USD and COP values greater than 0.",
    );
  }
  if (item.prepTimeMinutes <= 0 || item.prepTimeMinutes > 60) {
    errors.push("Menu item prepTimeMinutes must be between 1 and 60.");
  }
  if (!item.isAvailableInColombia && !item.isAvailableInUSA) {
    errors.push("Menu item must be available in at least one country.");
  }
  return result(errors);
};

export const validateSaleTransaction = (
  sale: SaleTransaction,
): ValidationResult => {
  const errors: string[] = [];
  if (sale.quantity <= 0) errors.push("Sale quantity must be greater than 0.");
  if (!hasPositivePrices(sale.totalPrice)) {
    errors.push("Sale totalPrice must have USD and COP values greater than 0.");
  }
  if (!hasText(sale.waiterName)) {
    errors.push("Sale waiterName must not be empty.");
  }
  return result(errors);
};

export const validateLocation = (location: Location): ValidationResult => {
  const errors: string[] = [];
  const currentYear = new Date().getFullYear();
  if (location.openingYear < 2008 || location.openingYear > currentYear) {
    errors.push(`Location openingYear must be between 2008 and ${currentYear}.`);
  }
  if (location.seatingCapacity <= 0) {
    errors.push("Location seatingCapacity must be greater than 0.");
  }
  if (location.staffCount <= 0) {
    errors.push("Location staffCount must be greater than 0.");
  }
  if (!hasPositivePrices(location.monthlyRentCost)) {
    errors.push("Location monthlyRentCost must have positive USD and COP values.");
  }
  if (!hasPositivePrices(location.averageMonthlyUtilities)) {
    errors.push(
      "Location averageMonthlyUtilities must have positive USD and COP values.",
    );
  }
  return result(errors);
};
