import useSWR from 'swr';
import type { PaginatedReservationsApi } from '@/types/booking';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

export function useMyReservations(limit = 50) {
  const { data, isLoading, mutate } = useSWR<PaginatedReservationsApi>(
    `/api/reservations?limit=${limit}&offset=0`,
    fetcher
  );

  return {
    reservations: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}
