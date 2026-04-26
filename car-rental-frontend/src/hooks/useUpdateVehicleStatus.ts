'use client';

import { useState } from 'react';
import type { VehicleStatus } from '@/types/vehicle';

export interface MaintenancePeriod {
  startDate: string;
  endDate: string;
  notes?: string;
}

export interface UpdateVehicleStatusInput {
  vehicleId: string;
  status: VehicleStatus;
  period?: MaintenancePeriod;
}

/**
 * Placeholder mutation — backend has no endpoint yet.
 * When `PATCH /api/vehicles/{id}/status` lands, replace the simulated delay
 * with a real fetch. The hook contract stays the same.
 */
export function useUpdateVehicleStatus() {
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function updateStatus(input: UpdateVehicleStatusInput): Promise<void> {
    setLoadingId(input.vehicleId);
    setError(null);
    try {
      // TODO: replace with real call once backend exposes the endpoint
      // await fetch(`/api/vehicles/${input.vehicleId}/status`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   credentials: 'include',
      //   body: JSON.stringify({ status: input.status, period: input.period ?? null }),
      // });
      await new Promise((resolve) => setTimeout(resolve, 400));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update status';
      setError(message);
      throw err;
    } finally {
      setLoadingId(null);
    }
  }

  return { updateStatus, loadingId, error };
}
