import { useEffect } from 'react';
import useSWR from 'swr';
import { listReviewableRentals, subscribe } from '@/data/reviews/mockStore';
import { mapReviewableRental, type ReviewableRental } from '@/types/review';

export function useReviewableRentals(): {
  rentals: ReviewableRental[];
  isLoading: boolean;
  refresh: () => void;
} {
  const { data, isLoading, mutate } = useSWR('reviewable-rentals', async () => {
    const api = listReviewableRentals();
    return api.map(mapReviewableRental);
  });

  useEffect(() => subscribe(() => mutate()), [mutate]);

  return {
    rentals: data ?? [],
    isLoading,
    refresh: () => mutate(),
  };
}
