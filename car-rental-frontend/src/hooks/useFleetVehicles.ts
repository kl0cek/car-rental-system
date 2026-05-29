import useSWR from 'swr';
import type {
  PaginatedVehiclesApi,
  VehicleStatus,
  SortableField,
  EngineType,
  CategoryName,
} from '@/types/vehicle';
import { mapVehicle } from '@/types/vehicle';

const FLEET_PAGE_SIZE = 15;

export interface FleetParams {
  status: VehicleStatus | null;
  page: number;
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
  search?: string;
  engineType?: EngineType | null;
  category?: CategoryName | null;
}

function buildQuery(params: FleetParams): string {
  const p = new URLSearchParams();
  p.set('offset', String((params.page - 1) * FLEET_PAGE_SIZE));
  p.set('limit', String(FLEET_PAGE_SIZE));
  p.set('sort_by', params.sortBy);
  p.set('sort_order', params.sortOrder);
  if (params.status) p.set('status', params.status);
  if (params.search) p.set('search', params.search);
  if (params.engineType) p.set('engine_type', params.engineType);
  if (params.category) p.set('category', params.category);
  return p.toString();
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error('Failed to fetch');
    return r.json() as Promise<PaginatedVehiclesApi>;
  });

export function useFleetVehicles(params: FleetParams) {
  const { data, isLoading, mutate } = useSWR(`/api/vehicles?${buildQuery(params)}`, fetcher, {
    keepPreviousData: true,
  });

  return {
    vehicles: data?.items.map(mapVehicle) ?? [],
    total: data?.total ?? 0,
    totalPages: Math.max(1, Math.ceil((data?.total ?? 0) / FLEET_PAGE_SIZE)),
    isLoading,
    refresh: mutate,
  };
}

export { FLEET_PAGE_SIZE };
