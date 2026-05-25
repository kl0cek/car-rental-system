'use client';

import useSWR from 'swr';
import {
  mapServiceOrder,
  type ServiceOrder,
  type VehicleServiceTimelineApi,
} from '@/types/serviceOrder';

const fetcher = (url: string): Promise<VehicleServiceTimelineApi> =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch timeline (${res.status})`);
    return res.json();
  });

export function useVehicleServiceTimeline(vehicleId: string | null | undefined): {
  orders: ServiceOrder[];
  isLoading: boolean;
  error: unknown;
  mutate: () => void;
} {
  const url = vehicleId ? `/api/vehicles/${vehicleId}/service-orders` : null;
  const { data, isLoading, error, mutate } = useSWR<VehicleServiceTimelineApi>(url, fetcher);

  return {
    orders: data ? data.orders.map(mapServiceOrder) : [],
    isLoading,
    error,
    mutate: () => {
      void mutate();
    },
  };
}
