import useSWR from 'swr';
import type { PaginatedUserRentalsApi } from '@/types/rental';
import type { ReviewableRental } from '@/types/review';

const ENDPOINT =
  '/api/users/me/rentals?status=completed&limit=100&offset=0&sort_by=pickup_date&sort_order=desc';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch rentals (${res.status})`);
    return res.json() as Promise<PaginatedUserRentalsApi>;
  });

/**
 * Reviewable rentals are the completed rentals of the current user. The
 * backend has no "already-reviewed?" hint per rental — the UI can attempt to
 * POST and surface 409 to the user if a duplicate is detected.
 */
export function useReviewableRentals(): {
  rentals: ReviewableRental[];
  isLoading: boolean;
  error: Error | undefined;
  refresh: () => void;
} {
  const { data, isLoading, error, mutate } = useSWR(ENDPOINT, fetcher);

  const rentals: ReviewableRental[] = (data?.items ?? [])
    // Defence-in-depth: backend filter already restricts to completed, but if
    // the query param semantics ever change we still want to avoid offering
    // reviews on in-progress rentals.
    .filter((item) => item.status === 'completed' && item.return_date !== null)
    .map((item) => ({
      rentalId: item.id,
      vehicleId: item.vehicle.id,
      vehicleBrand: item.vehicle.brand,
      vehicleModel: item.vehicle.model,
      vehicleImageUrl: item.vehicle.image_url,
      returnDate: item.return_date as string,
    }));

  return {
    rentals,
    isLoading,
    error: error as Error | undefined,
    refresh: () => mutate(),
  };
}
