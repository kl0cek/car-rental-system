'use client';

import { useState } from 'react';
import type {
  CategoryName,
  EngineType,
  VehicleColor,
  VehicleDetail,
  VehicleDetailApi,
  VehicleStatus,
} from '@/types/vehicle';
import { mapVehicleDetail } from '@/types/vehicle';

export interface UpdateVehicleInput {
  brand?: string;
  model?: string;
  year?: number;
  licensePlate?: string;
  vin?: string;
  color?: VehicleColor;
  categoryId?: string;
  category?: CategoryName;
  engineType?: EngineType;
  horsepower?: number;
  seats?: number;
  trunkCapacity?: number;
  mileage?: number;
  dailyBasePrice?: number;
  status?: VehicleStatus;
}

function append(form: FormData, key: string, value: string | number | undefined): void {
  if (value === undefined || value === null || value === '') return;
  form.append(key, String(value));
}

/**
 * Updates scalar fields of a vehicle. Image management lives in dedicated
 * hooks (useVehicleImages) — keeping responsibilities separate avoids the
 * brittle "edit + upload" mega-form pattern.
 */
export function useUpdateVehicle() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function updateVehicle(id: string, input: UpdateVehicleInput): Promise<VehicleDetail> {
    setIsLoading(true);
    setError(null);
    try {
      const form = new FormData();
      append(form, 'brand', input.brand);
      append(form, 'model', input.model);
      append(form, 'year', input.year);
      append(form, 'license_plate', input.licensePlate);
      append(form, 'vin', input.vin);
      append(form, 'engine_type', input.engineType);
      append(form, 'horsepower', input.horsepower);
      append(form, 'seats', input.seats);
      append(form, 'trunk_capacity', input.trunkCapacity);
      append(form, 'daily_base_price', input.dailyBasePrice);
      append(form, 'color', input.color);
      append(form, 'category_id', input.categoryId);
      append(form, 'mileage', input.mileage);
      append(form, 'status', input.status);

      const res = await fetch(`/api/admin/vehicles/${id}`, {
        method: 'PUT',
        credentials: 'include',
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Update vehicle failed (${res.status}): ${text}`);
      }
      return mapVehicleDetail((await res.json()) as VehicleDetailApi);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update vehicle';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { updateVehicle, isLoading, error };
}
