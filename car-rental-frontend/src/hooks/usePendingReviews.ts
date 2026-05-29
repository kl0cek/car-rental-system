import useSWR from 'swr';
import {
  mapPaginatedReviews,
  type PaginatedReviews,
  type PaginatedReviewsApi,
} from '@/types/review';

interface UsePendingReviewsParams {
  page: number;
  pageSize?: number;
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch reviews (${res.status})`);
    return res.json() as Promise<PaginatedReviewsApi>;
  });

/**
 * Admin flat listing across all vehicles. The backend has no moderation
 * pipeline (no pending/approved/rejected states) — the moderation page can
 * only delete reviews, not approve / reject / flag.
 */
export function usePendingReviews({ page, pageSize = 10 }: UsePendingReviewsParams): {
  data: PaginatedReviews | null;
  isLoading: boolean;
  error: Error | undefined;
  refresh: () => void;
  pageSize: number;
} {
  const offset = (page - 1) * pageSize;
  const key = `/api/reviews?offset=${offset}&limit=${pageSize}`;

  const { data, isLoading, error, mutate } = useSWR(key, fetcher, { keepPreviousData: true });

  return {
    data: data ? mapPaginatedReviews(data) : null,
    isLoading,
    error: error as Error | undefined,
    refresh: () => mutate(),
    pageSize,
  };
}
