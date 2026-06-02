import useSWR from 'swr';

interface AvailabilityResponse {
  vehicle_id: string;
  available: boolean;
  start_date: string;
  end_date: string;
  conflicting_rentals: number;
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch availability');
    return res.json();
  });

export function useVehicleAvailability(vehicleId: string, startDate: string, endDate: string) {
  const enabled = !!startDate && !!endDate;
  const key = enabled
    ? `/api/vehicles/${vehicleId}/availability?start_date=${startDate}&end_date=${endDate}`
    : null;

  const { data, isLoading, error } = useSWR<AvailabilityResponse>(key, fetcher);

  return {
    available: enabled ? (data?.available ?? null) : null,
    conflictingRentals: data?.conflicting_rentals ?? 0,
    isLoading: enabled && isLoading,
    error,
  };
}
