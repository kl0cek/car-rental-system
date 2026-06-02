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

export interface CreateVehicleInput {
  brand: string;
  model: string;
  year: number;
  licensePlate: string;
  vin: string;
  color: VehicleColor;
  categoryId: string;
  category: CategoryName; // kept for parity with existing form code; not sent
  engineType: EngineType;
  horsepower: number;
  seats: number;
  trunkCapacity: number;
  mileage: number;
  dailyBasePrice: number;
  status?: VehicleStatus;
  images: File[];
}

function appendField(form: FormData, key: string, value: string | number | undefined): void {
  if (value === undefined || value === null || value === '') return;
  form.append(key, String(value));
}

export function useCreateVehicle() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createVehicle(input: CreateVehicleInput): Promise<VehicleDetail> {
    setIsLoading(true);
    setError(null);
    try {
      const form = new FormData();
      appendField(form, 'brand', input.brand);
      appendField(form, 'model', input.model);
      appendField(form, 'year', input.year);
      appendField(form, 'license_plate', input.licensePlate);
      appendField(form, 'vin', input.vin);
      appendField(form, 'engine_type', input.engineType);
      appendField(form, 'horsepower', input.horsepower);
      appendField(form, 'seats', input.seats);
      appendField(form, 'trunk_capacity', input.trunkCapacity);
      appendField(form, 'daily_base_price', input.dailyBasePrice);
      appendField(form, 'color', input.color);
      appendField(form, 'category_id', input.categoryId);
      appendField(form, 'mileage', input.mileage);
      if (input.status) appendField(form, 'status', input.status);
      for (const file of input.images) {
        form.append('images', file);
      }

      const res = await fetch('/api/admin/vehicles', {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Create vehicle failed (${res.status}): ${text}`);
      }
      return mapVehicleDetail((await res.json()) as VehicleDetailApi);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to create vehicle';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { createVehicle, isLoading, error };
}
