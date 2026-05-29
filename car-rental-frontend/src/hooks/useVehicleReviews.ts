import { useEffect } from 'react';
import useSWR from 'swr';
import { mapPaginatedReviews, type PaginatedReviews, type ReviewSort } from '@/types/review';
import { listVehicleReviews, subscribe } from '@/data/reviews/mockStore';

const PAGE_SIZE = 5;

interface UseVehicleReviewsParams {
  vehicleId: string | null | undefined;
  sort: ReviewSort;
  page: number;
}

function fakeNetworkDelay<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 200));
}

export function useVehicleReviews({ vehicleId, sort, page }: UseVehicleReviewsParams): {
  data: PaginatedReviews | null;
  isLoading: boolean;
  error: Error | undefined;
  refresh: () => void;
  pageSize: number;
} {
  const key = vehicleId ? ['reviews', vehicleId, sort, page] : null;

  const { data, isLoading, error, mutate } = useSWR(
    key,
    async () => {
      const api = listVehicleReviews({
        vehicleId: vehicleId!,
        sort,
        offset: (page - 1) * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      return fakeNetworkDelay(mapPaginatedReviews(api));
    },
    { keepPreviousData: true }
  );

  useEffect(() => subscribe(() => mutate()), [mutate]);

  return {
    data: data ?? null,
    isLoading,
    error: error as Error | undefined,
    refresh: () => mutate(),
    pageSize: PAGE_SIZE,
  };
}
