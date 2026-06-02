'use client';

import { useState } from 'react';
import type { VehicleStatus } from '@/types/vehicle';

export interface BulkStatusResult {
  updated: number;
  notFound: string[];
}

interface ApiResponse {
  updated: number;
  not_found: string[];
}

/**
 * Calls PATCH /api/admin/vehicles/bulk-status with a batch of ids and a target status.
 * Returns the count of updated rows + ids the backend couldn't find (soft-deleted or missing).
 */
export function useBulkUpdateVehicleStatus() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function bulkUpdate(ids: string[], status: VehicleStatus): Promise<BulkStatusResult> {
    if (ids.length === 0) return { updated: 0, notFound: [] };
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/admin/vehicles/bulk-status', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ids, status }),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Bulk update failed (${res.status}): ${text}`);
      }
      const body = (await res.json()) as ApiResponse;
      return { updated: body.updated, notFound: body.not_found };
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Bulk update failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { bulkUpdate, isLoading, error };
}
