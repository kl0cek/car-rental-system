import useSWR from 'swr';
import type { PaginatedVehiclesApi, VehicleStatus, SortableField } from '@/types/vehicle';
import { mapVehicle } from '@/types/vehicle';

const FLEET_PAGE_SIZE = 15;

export interface FleetParams {
  status: VehicleStatus | null;
  page: number;
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
}

function buildQuery(params: FleetParams): string {
  const p = new URLSearchParams();
  p.set('offset', String((params.page - 1) * FLEET_PAGE_SIZE));
  p.set('limit', String(FLEET_PAGE_SIZE));
  p.set('sort_by', params.sortBy);
  p.set('sort_order', params.sortOrder);
  if (params.status) p.set('status', params.status);
  return p.toString();
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error('Failed to fetch');
    return r.json() as Promise<PaginatedVehiclesApi>;
  });

export function useFleetVehicles(params: FleetParams) {
  const { data, isLoading } = useSWR(`/api/vehicles?${buildQuery(params)}`, fetcher, {
    keepPreviousData: true,
  });

  return {
    vehicles: data?.items.map(mapVehicle) ?? [],
    total: data?.total ?? 0,
    totalPages: Math.max(1, Math.ceil((data?.total ?? 0) / FLEET_PAGE_SIZE)),
    isLoading,
  };
}

export { FLEET_PAGE_SIZE };
