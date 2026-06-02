import useSWR from 'swr';
import type { VehicleDetail, VehicleDetailApi } from '@/types/vehicle';
import { mapVehicleDetail } from '@/types/vehicle';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error(`Failed to fetch vehicle (${r.status})`);
    return r.json() as Promise<VehicleDetailApi>;
  });

export function useVehicleDetail(vehicleId: string | null | undefined) {
  const key = vehicleId ? `/api/vehicles/${vehicleId}` : null;
  const { data, isLoading, error, mutate } = useSWR(key, fetcher);

  return {
    vehicle: data ? mapVehicleDetail(data) : null,
    isLoading,
    error: error as Error | undefined,
    refresh: mutate,
  };
}

export type { VehicleDetail };
