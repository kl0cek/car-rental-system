'use client';

import useSWR from 'swr';
import {
  mapServiceOrderStats,
  type ServiceOrderStats,
  type ServiceOrderStatsApi,
} from '@/types/serviceOrder';

const fetcher = (url: string): Promise<ServiceOrderStatsApi> =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch stats (${res.status})`);
    return res.json();
  });

export function useServiceOrderStats(): {
  stats: ServiceOrderStats | undefined;
  isLoading: boolean;
  mutate: () => void;
} {
  const { data, isLoading, mutate } = useSWR<ServiceOrderStatsApi>(
    '/api/service-orders/stats',
    fetcher,
  );
  return {
    stats: data ? mapServiceOrderStats(data) : undefined,
    isLoading,
    mutate: () => {
      void mutate();
    },
  };
}
