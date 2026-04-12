import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { FiltersState } from '@/components/vehicles/VehicleFilters';
import { PRICE_MIN, PRICE_MAX, YEAR_MIN, YEAR_MAX } from '@/types/vehicle';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function isDefaultFilters(filters: FiltersState): boolean {
  return (
    !filters.category &&
    !filters.engineType &&
    filters.priceRange[0] === PRICE_MIN &&
    filters.priceRange[1] === PRICE_MAX &&
    filters.yearRange[0] === YEAR_MIN &&
    filters.yearRange[1] === YEAR_MAX &&
    !filters.minSeats &&
    !filters.availableFrom &&
    !filters.availableTo
  );
}

export function getDefaultFilters(): Partial<FiltersState> {
  return {
    category: null,
    engineType: null,
    priceRange: [PRICE_MIN, PRICE_MAX],
    yearRange: [YEAR_MIN, YEAR_MAX],
    minSeats: null,
    availableFrom: '',
    availableTo: '',
  };
}
