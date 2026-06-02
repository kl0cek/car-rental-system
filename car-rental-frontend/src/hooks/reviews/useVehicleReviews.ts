import { useMemo } from 'react';
import useSWR from 'swr';
import {
  mapPaginatedReviews,
  type PaginatedReviews,
  type PaginatedReviewsApi,
  type Review,
  type ReviewSort,
} from '@/types/review';

const PAGE_SIZE = 5;

interface UseVehicleReviewsParams {
  vehicleId: string | null | undefined;
  sort: ReviewSort;
  page: number;
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch reviews (${res.status})`);
    return res.json() as Promise<PaginatedReviewsApi>;
  });

function sortItems(items: Review[], sort: ReviewSort): Review[] {
  if (sort === 'newest') return items;
  const copy = [...items];
  if (sort === 'top_rating') {
    copy.sort((a, b) => b.rating - a.rating || b.createdAt.localeCompare(a.createdAt));
  } else if (sort === 'low_rating') {
    copy.sort((a, b) => a.rating - b.rating || b.createdAt.localeCompare(a.createdAt));
  }
  return copy;
}

export function useVehicleReviews({ vehicleId, sort, page }: UseVehicleReviewsParams): {
  data: PaginatedReviews | null;
  isLoading: boolean;
  error: Error | undefined;
  refresh: () => void;
  pageSize: number;
} {
  const offset = (page - 1) * PAGE_SIZE;
  // The backend lists newest-first; non-newest sorts are applied client-side
  // on the current page slice. This matches the project's "no fancy server
  // sorting" stance for review listings and keeps the endpoint simple.
  const key = vehicleId
    ? `/api/vehicles/${vehicleId}/reviews?offset=${offset}&limit=${PAGE_SIZE}`
    : null;

  const { data, isLoading, error, mutate } = useSWR(key, fetcher, { keepPreviousData: true });

  const mapped = useMemo(() => {
    if (!data) return null;
    const mappedData = mapPaginatedReviews(data);
    return { ...mappedData, items: sortItems(mappedData.items, sort) };
  }, [data, sort]);

  return {
    data: mapped,
    isLoading,
    error: error as Error | undefined,
    refresh: () => mutate(),
    pageSize: PAGE_SIZE,
  };
}
