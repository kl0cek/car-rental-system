import useSWR from 'swr';
import type { PaginatedUserRentalsApi } from '@/types/rental';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

export function useMyRentals(limit = 5) {
  const { data, isLoading, mutate } = useSWR<PaginatedUserRentalsApi>(
    `/api/users/me/rentals?limit=${limit}&offset=0&sort_by=pickup_date&sort_order=desc`,
    fetcher
  );

  return {
    rentals: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}
