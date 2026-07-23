import type { Location, MenuItem } from "../types/models";

export const findLocationById = (
  locations: Location[],
  id: string,
): Location | null => {
  for (const location of locations) {
    if (location.id === id) return location;
  }
  return null;
};

export const findMenuItemByName = (
  items: MenuItem[],
  name: string,
): MenuItem | null => {
  const normalizedName = name.trim().toLocaleLowerCase();
  for (const item of items) {
    if (item.name.toLocaleLowerCase() === normalizedName) return item;
  }
  return null;
};

export const binarySearchLocationByCapacity = (
  sortedLocations: Location[],
  targetCapacity: number,
): number => {
  let left = 0;
  let right = sortedLocations.length - 1;

  while (left <= right) {
    const middle = Math.floor((left + right) / 2);
    const capacity = sortedLocations[middle].seatingCapacity;
    if (capacity === targetCapacity) return middle;
    if (capacity < targetCapacity) left = middle + 1;
    else right = middle - 1;
  }

  return -1;
};
