import { useEffect } from 'react';
import useSWR from 'swr';
import { listForModeration, subscribe, type ModerationQuery } from '@/data/reviews/mockStore';
import { mapPaginatedReviews, type PaginatedReviews } from '@/types/review';

interface UsePendingReviewsParams {
  status: ModerationQuery['status'];
  page: number;
  pageSize?: number;
}

export function usePendingReviews({ status, page, pageSize = 10 }: UsePendingReviewsParams): {
  data: PaginatedReviews | null;
  isLoading: boolean;
  refresh: () => void;
  pageSize: number;
} {
  const { data, isLoading, mutate } = useSWR(
    ['pending-reviews', status, page, pageSize],
    async () => {
      const api = listForModeration({
        status,
        offset: (page - 1) * pageSize,
        limit: pageSize,
      });
      return mapPaginatedReviews(api);
    },
    { keepPreviousData: true }
  );

  useEffect(() => subscribe(() => mutate()), [mutate]);

  return {
    data: data ?? null,
    isLoading,
    refresh: () => mutate(),
    pageSize,
  };
}
