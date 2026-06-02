import useSWR from 'swr';

interface VehicleDetailApi {
  booked_dates: Array<{ start_date: string; end_date: string }>;
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

export function useVehicleBookedDates(vehicleId: string) {
  const { data, isLoading } = useSWR<VehicleDetailApi>(`/api/vehicles/${vehicleId}`, fetcher);

  const bookedRanges: Array<[string, string]> =
    data?.booked_dates.map((r) => [r.start_date.slice(0, 10), r.end_date.slice(0, 10)]) ?? [];

  return { bookedRanges, isLoading };
}
