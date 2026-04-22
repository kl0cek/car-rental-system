import useSWR from 'swr';
import type { PaginatedAdminReservationsApi } from '@/types/rental';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

export function useAdminReservations(limit = 50) {
  const { data, isLoading, mutate } = useSWR<PaginatedAdminReservationsApi>(
    `/api/admin/reservations?limit=${limit}&offset=0&sort_by=created_at&sort_order=desc`,
    fetcher
  );

  return {
    reservations: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}
