'use client';

import useSWR from 'swr';
import {
  mapPaginatedServiceOrders,
  type PaginatedServiceOrders,
  type PaginatedServiceOrdersApi,
  type ServiceOrderStatus,
  type ServiceType,
} from '@/types/serviceOrder';

const fetcher = (url: string): Promise<PaginatedServiceOrdersApi> =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch service orders (${res.status})`);
    return res.json();
  });

export interface ServiceOrderFilters {
  status?: ServiceOrderStatus;
  type?: ServiceType;
  vehicleId?: string;
  technicianId?: string;
  scheduledFrom?: string;
  scheduledTo?: string;
  offset?: number;
  limit?: number;
  sortBy?: 'scheduled_date' | 'completed_date' | 'created_at' | 'cost';
  sortOrder?: 'asc' | 'desc';
}

function buildQuery(filters: ServiceOrderFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.type) params.set('type', filters.type);
  if (filters.vehicleId) params.set('vehicle_id', filters.vehicleId);
  if (filters.technicianId) params.set('technician_id', filters.technicianId);
  if (filters.scheduledFrom) params.set('scheduled_from', filters.scheduledFrom);
  if (filters.scheduledTo) params.set('scheduled_to', filters.scheduledTo);
  if (filters.offset !== undefined) params.set('offset', String(filters.offset));
  if (filters.limit !== undefined) params.set('limit', String(filters.limit));
  if (filters.sortBy) params.set('sort_by', filters.sortBy);
  if (filters.sortOrder) params.set('sort_order', filters.sortOrder);
  return params.toString();
}

export function useServiceOrders(filters: ServiceOrderFilters = {}): {
  data: PaginatedServiceOrders | undefined;
  isLoading: boolean;
  error: unknown;
  mutate: () => void;
} {
  const qs = buildQuery(filters);
  const url = qs ? `/api/service-orders?${qs}` : '/api/service-orders';
  const { data, isLoading, error, mutate } = useSWR<PaginatedServiceOrdersApi>(url, fetcher);

  return {
    data: data ? mapPaginatedServiceOrders(data) : undefined,
    isLoading,
    error,
    mutate: () => {
      void mutate();
    },
  };
}
