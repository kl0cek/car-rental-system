'use client';

import { useState } from 'react';
import type { VehicleDetail, VehicleDetailApi } from '@/types/vehicle';
import { mapVehicleDetail } from '@/types/vehicle';

async function asJson(res: Response): Promise<VehicleDetail> {
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Image op failed (${res.status}): ${text}`);
  }
  return mapVehicleDetail((await res.json()) as VehicleDetailApi);
}

/**
 * Manage vehicle gallery: upload, delete, set primary, reorder.
 * Each operation returns the fresh VehicleDetail so the caller can update
 * UI state without a separate refetch.
 */
export function useVehicleImages() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run<T>(fn: () => Promise<T>): Promise<T> {
    setIsLoading(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Image operation failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  async function uploadImage(
    vehicleId: string,
    file: File,
    isPrimary: boolean
  ): Promise<VehicleDetail> {
    return run(async () => {
      const form = new FormData();
      form.append('image', file);
      form.append('is_primary', String(isPrimary));
      const res = await fetch(`/api/admin/vehicles/${vehicleId}/images`, {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      return asJson(res);
    });
  }

  async function deleteImage(vehicleId: string, imageId: string): Promise<VehicleDetail> {
    return run(async () => {
      const res = await fetch(`/api/admin/vehicles/${vehicleId}/images/${imageId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      return asJson(res);
    });
  }

  async function setPrimary(vehicleId: string, imageId: string): Promise<VehicleDetail> {
    return run(async () => {
      const res = await fetch(`/api/admin/vehicles/${vehicleId}/images/${imageId}/primary`, {
        method: 'POST',
        credentials: 'include',
      });
      return asJson(res);
    });
  }

  async function reorder(vehicleId: string, orderedIds: string[]): Promise<VehicleDetail> {
    return run(async () => {
      const res = await fetch(`/api/admin/vehicles/${vehicleId}/images/order`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(orderedIds),
      });
      return asJson(res);
    });
  }

  return { uploadImage, deleteImage, setPrimary, reorder, isLoading, error };
}
