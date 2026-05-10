import { isDefaultFilters, getDefaultFilters } from '@/lib/filters';
import { PRICE_MIN, PRICE_MAX, YEAR_MIN, YEAR_MAX } from '@/types/vehicle';
import type { FiltersState } from '@/components/vehicles/VehicleFilters';

const defaults: FiltersState = {
  category: null,
  engineType: null,
  priceRange: [PRICE_MIN, PRICE_MAX],
  yearRange: [YEAR_MIN, YEAR_MAX],
  minSeats: null,
  availableFrom: '',
  availableTo: '',
  sortBy: 'created_at',
  sortOrder: 'desc',
};

describe('isDefaultFilters', () => {
  it('true for fresh defaults', () => {
    expect(isDefaultFilters(defaults)).toBe(true);
  });

  it.each<[string, Partial<FiltersState>]>([
    ['category set', { category: 'suv' }],
    ['engineType set', { engineType: 'electric' }],
    ['minSeats set', { minSeats: 5 }],
    ['priceRange narrowed lo', { priceRange: [100, PRICE_MAX] }],
    ['priceRange narrowed hi', { priceRange: [PRICE_MIN, 500] }],
    ['yearRange narrowed', { yearRange: [2010, YEAR_MAX] }],
    ['availableFrom set', { availableFrom: '2026-05-01' }],
    ['availableTo set', { availableTo: '2026-05-10' }],
  ])('false when %s', (_label, override) => {
    expect(isDefaultFilters({ ...defaults, ...override })).toBe(false);
  });
});

describe('getDefaultFilters', () => {
  it('returns object that satisfies isDefaultFilters', () => {
    const d = getDefaultFilters() as FiltersState;
    expect(isDefaultFilters(d)).toBe(true);
  });
});
