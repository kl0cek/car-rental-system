import useSWR from 'swr';
import type {
  PaginatedVehiclesApi,
  CategoryName,
  EngineType,
  SortableField,
} from '@/types/vehicle';
import { mapVehicle, PRICE_MIN, PRICE_MAX, YEAR_MIN, YEAR_MAX, PAGE_SIZE } from '@/types/vehicle';

export interface VehicleSearchParams {
  category: CategoryName | null;
  engineType: EngineType | null;
  priceRange: [number, number];
  yearRange: [number, number];
  minSeats: number | null;
  availableFrom: string;
  availableTo: string;
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
  page: number;
}

function buildQuery(params: VehicleSearchParams): string {
  const p = new URLSearchParams();

  p.set('offset', String((params.page - 1) * PAGE_SIZE));
  p.set('limit', String(PAGE_SIZE));
  p.set('sort_by', params.sortBy);
  p.set('sort_order', params.sortOrder);

  if (params.category) p.set('category', params.category);
  if (params.engineType) p.set('engine_type', params.engineType);

  if (params.priceRange[0] > PRICE_MIN) p.set('min_price', String(params.priceRange[0]));
  if (params.priceRange[1] < PRICE_MAX) p.set('max_price', String(params.priceRange[1]));

  if (params.yearRange[0] > YEAR_MIN) p.set('min_year', String(params.yearRange[0]));
  if (params.yearRange[1] < YEAR_MAX) p.set('max_year', String(params.yearRange[1]));

  if (params.minSeats) p.set('min_seats', String(params.minSeats));

  if (params.availableFrom && params.availableTo && params.availableFrom <= params.availableTo) {
    p.set('available_from', params.availableFrom);
    p.set('available_to', params.availableTo);
  }

  return p.toString();
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error('Failed to fetch vehicles');
    return r.json() as Promise<PaginatedVehiclesApi>;
  });

export function useVehicles(params: VehicleSearchParams, options?: { enabled?: boolean }) {
  const enabled = options?.enabled ?? true;
  const query = buildQuery(params);
  const { data, error, isLoading } = useSWR(enabled ? `/api/vehicles?${query}` : null, fetcher, {
    keepPreviousData: true,
  });

  return {
    vehicles: data?.items.map(mapVehicle) ?? [],
    total: data?.total ?? 0,
    isLoading: enabled && isLoading,
    isError: !!error,
  };
}
