import { Location, MenuItem } from "../types/models";

export const findLocationById = (locations: Location[], id: string): Location | null => {
  for (const location of locations) {
    if (location.id === id) {
      return location;
    }
  }

  return null;
};

export const findMenuItemByName = (items: MenuItem[], name: string): MenuItem | null => {
  const normalizedName = name.trim().toLocaleLowerCase();

  for (const item of items) {
    if (item.name.toLocaleLowerCase() === normalizedName) {
      return item;
    }
  }

  return null;
};

export const binarySearchLocationByCapacity = (
  sortedLocations: Location[],
  targetCapacity: number,
): number => {
  let leftIndex = 0;
  let rightIndex = sortedLocations.length - 1;

  while (leftIndex <= rightIndex) {
    const middleIndex = Math.floor((leftIndex + rightIndex) / 2);
    const middleCapacity = sortedLocations[middleIndex].seatingCapacity;

    if (middleCapacity === targetCapacity) {
      return middleIndex;
    }

    if (middleCapacity < targetCapacity) {
      leftIndex = middleIndex + 1;
    } else {
      rightIndex = middleIndex - 1;
    }
  }

  return -1;
};