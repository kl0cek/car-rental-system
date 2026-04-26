'use client';

import useSWR from 'swr';
import { useCallback, useMemo, useState } from 'react';
import { mapVehicle, type PaginatedVehiclesApi, type Vehicle, type VehicleStatus } from '@/types/vehicle';
import type { MaintenancePeriod } from './useUpdateVehicleStatus';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

export interface MaintenanceVehicle extends Vehicle {
  maintenancePeriod?: MaintenancePeriod;
}

interface LocalOverride {
  status: VehicleStatus;
  period?: MaintenancePeriod;
}

/**
 * Backend has no status-update endpoint yet, so this hook holds an in-memory
 * map of vehicleId -> local override that wins over the API status. Once the
 * mutation goes through to the server, the override layer can be removed.
 */
export function useMaintenanceVehicles() {
  const { data, isLoading, mutate } = useSWR<PaginatedVehiclesApi>(
    '/api/vehicles?limit=100&offset=0',
    fetcher
  );

  const [overrides, setOverrides] = useState<Record<string, LocalOverride>>({});

  const vehicles: MaintenanceVehicle[] = useMemo(() => {
    const items = data?.items.map(mapVehicle) ?? [];
    return items.map((v) => {
      const override = overrides[v.id];
      if (!override) return v;
      return { ...v, status: override.status, maintenancePeriod: override.period };
    });
  }, [data, overrides]);

  const setOverride = useCallback(
    (vehicleId: string, status: VehicleStatus, period?: MaintenancePeriod) => {
      setOverrides((prev) => ({ ...prev, [vehicleId]: { status, period } }));
    },
    []
  );

  return { vehicles, isLoading, mutate, setOverride };
}
