'use client';

import { useCallback, useState } from 'react';
import { mutate as globalMutate } from 'swr';
import {
  mapServiceOrder,
  type AddServiceHistoryPayload,
  type CreateServiceOrderPayload,
  type ServiceOrder,
  type ServiceOrderApi,
  type ServiceOrderStatus,
  type UpdateServiceOrderPayload,
} from '@/types/serviceOrder';

function revalidateServiceOrderLists(): void {
  // Invalidate every SWR cache key touching service orders so the list,
  // stats, and vehicle timelines refresh after a successful mutation.
  globalMutate(
    (key) =>
      typeof key === 'string' &&
      (key.startsWith('/api/service-orders') ||
        (key.startsWith('/api/vehicles/') && key.endsWith('/service-orders'))),
  );
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
    // fall through
  }
  return `Request failed (${res.status})`;
}

interface MutationState {
  isSubmitting: boolean;
  error: string | null;
}

function snakeCaseCreate(payload: CreateServiceOrderPayload) {
  return {
    vehicle_id: payload.vehicleId,
    type: payload.type,
    description: payload.description,
    cost: payload.cost === null ? null : payload.cost,
    scheduled_date: payload.scheduledDate,
    technician_id: payload.technicianId,
  };
}

function snakeCaseUpdate(payload: UpdateServiceOrderPayload) {
  const body: Record<string, unknown> = {};
  if (payload.type !== undefined) body.type = payload.type;
  if (payload.description !== undefined) body.description = payload.description;
  if (payload.cost !== undefined) body.cost = payload.cost;
  if (payload.scheduledDate !== undefined) body.scheduled_date = payload.scheduledDate;
  if (payload.technicianId !== undefined) body.technician_id = payload.technicianId;
  return body;
}

export function useCreateServiceOrder(): {
  submit: (payload: CreateServiceOrderPayload) => Promise<ServiceOrder>;
} & MutationState {
  const [state, setState] = useState<MutationState>({ isSubmitting: false, error: null });

  const submit = useCallback(async (payload: CreateServiceOrderPayload) => {
    setState({ isSubmitting: true, error: null });
    try {
      const res = await fetch('/api/service-orders', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(snakeCaseCreate(payload)),
      });
      if (!res.ok) {
        const message = await readError(res);
        setState({ isSubmitting: false, error: message });
        throw new Error(message);
      }
      const api = (await res.json()) as ServiceOrderApi;
      revalidateServiceOrderLists();
      setState({ isSubmitting: false, error: null });
      return mapServiceOrder(api);
    } catch (err) {
      if (!(err instanceof Error)) setState({ isSubmitting: false, error: 'Unknown error' });
      throw err;
    }
  }, []);

  return { submit, ...state };
}

export function useUpdateServiceOrder(): {
  submit: (id: string, payload: UpdateServiceOrderPayload) => Promise<ServiceOrder>;
} & MutationState {
  const [state, setState] = useState<MutationState>({ isSubmitting: false, error: null });

  const submit = useCallback(async (id: string, payload: UpdateServiceOrderPayload) => {
    setState({ isSubmitting: true, error: null });
    try {
      const res = await fetch(`/api/service-orders/${id}`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(snakeCaseUpdate(payload)),
      });
      if (!res.ok) {
        const message = await readError(res);
        setState({ isSubmitting: false, error: message });
        throw new Error(message);
      }
      const api = (await res.json()) as ServiceOrderApi;
      revalidateServiceOrderLists();
      setState({ isSubmitting: false, error: null });
      return mapServiceOrder(api);
    } catch (err) {
      if (!(err instanceof Error)) setState({ isSubmitting: false, error: 'Unknown error' });
      throw err;
    }
  }, []);

  return { submit, ...state };
}

export function useUpdateServiceOrderStatus(): {
  submit: (id: string, status: ServiceOrderStatus, cost?: number | null) => Promise<ServiceOrder>;
} & MutationState {
  const [state, setState] = useState<MutationState>({ isSubmitting: false, error: null });

  const submit = useCallback(
    async (id: string, status: ServiceOrderStatus, cost?: number | null) => {
      setState({ isSubmitting: true, error: null });
      try {
        const body: Record<string, unknown> = { status };
        if (cost !== undefined) body.cost = cost;
        const res = await fetch(`/api/service-orders/${id}/status`, {
          method: 'PUT',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        });
        if (!res.ok) {
          const message = await readError(res);
          setState({ isSubmitting: false, error: message });
          throw new Error(message);
        }
        const api = (await res.json()) as ServiceOrderApi;
        revalidateServiceOrderLists();
        setState({ isSubmitting: false, error: null });
        return mapServiceOrder(api);
      } catch (err) {
        if (!(err instanceof Error)) setState({ isSubmitting: false, error: 'Unknown error' });
        throw err;
      }
    },
    [],
  );

  return { submit, ...state };
}

export function useAddServiceHistory(): {
  submit: (orderId: string, payload: AddServiceHistoryPayload) => Promise<ServiceOrder>;
} & MutationState {
  const [state, setState] = useState<MutationState>({ isSubmitting: false, error: null });

  const submit = useCallback(async (orderId: string, payload: AddServiceHistoryPayload) => {
    setState({ isSubmitting: true, error: null });
    try {
      const res = await fetch(`/api/service-orders/${orderId}/history`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          service_order_id: orderId,
          notes: payload.notes,
          parts_replaced: payload.partsReplaced,
          mileage_at_service: payload.mileageAtService,
        }),
      });
      if (!res.ok) {
        const message = await readError(res);
        setState({ isSubmitting: false, error: message });
        throw new Error(message);
      }
      const api = (await res.json()) as ServiceOrderApi;
      revalidateServiceOrderLists();
      setState({ isSubmitting: false, error: null });
      return mapServiceOrder(api);
    } catch (err) {
      if (!(err instanceof Error)) setState({ isSubmitting: false, error: 'Unknown error' });
      throw err;
    }
  }, []);

  return { submit, ...state };
}
