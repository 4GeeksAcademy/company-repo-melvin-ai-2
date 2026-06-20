import { Location, MenuItem, Price, SaleTransaction, ValidationResult } from "../types/models";

const hasPositivePriceValues = (price: Price): boolean => {
  return price.USD > 0 && price.COP > 0;
};

const hasText = (value: string): boolean => {
  return value.trim().length > 0;
};

const buildValidationResult = (errors: string[]): ValidationResult => ({
  valid: errors.length === 0,
  errors,
});

export const validateMenuItem = (item: MenuItem): ValidationResult => {
  const errors: string[] = [];

  if (!hasText(item.name)) {
    errors.push("Menu item name must not be empty.");
  }

  if (!hasPositivePriceValues(item.basePrice)) {
    errors.push("Menu item basePrice must have USD and COP values greater than 0.");
  }

  if (!hasPositivePriceValues(item.ingredientCost)) {
    errors.push("Menu item ingredientCost must have USD and COP values greater than 0.");
  }

  if (item.prepTimeMinutes <= 0 || item.prepTimeMinutes > 60) {
    errors.push("Menu item prepTimeMinutes must be greater than 0 and less than or equal to 60.");
  }

  if (!item.isAvailableInColombia && !item.isAvailableInUSA) {
    errors.push("Menu item must be available in at least one country.");
  }

  return buildValidationResult(errors);
};

export const validateSaleTransaction = (sale: SaleTransaction): ValidationResult => {
  const errors: string[] = [];

  if (sale.quantity <= 0) {
    errors.push("Sale transaction quantity must be greater than 0.");
  }

  if (!hasPositivePriceValues(sale.totalPrice)) {
    errors.push("Sale transaction totalPrice must have USD and COP values greater than 0.");
  }

  if (!hasText(sale.waiterName)) {
    errors.push("Sale transaction waiterName must not be empty.");
  }

  return buildValidationResult(errors);
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

  if (!hasPositivePriceValues(location.monthlyRentCost)) {
    errors.push("Location monthlyRentCost must have USD and COP values greater than 0.");
  }

  if (!hasPositivePriceValues(location.averageMonthlyUtilities)) {
    errors.push("Location averageMonthlyUtilities must have USD and COP values greater than 0.");
  }

  return buildValidationResult(errors);
};