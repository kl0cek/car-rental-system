'use client';

import { useState } from 'react';
import type { CategoryName, EngineType } from '@/types/vehicle';

export interface CreateVehicleInput {
  brand: string;
  model: string;
  year: number;
  licensePlate: string;
  color: string;
  category: CategoryName;
  engineType: EngineType;
  horsepower: number;
  seats: number;
  trunkCapacity: number;
  mileage: number;
  dailyBasePrice: number;
  imageUrl: string | null;
}

/**
 * Placeholder mutation — backend has no admin vehicle-create endpoint.
 * Once `POST /api/admin/vehicles` is added, swap the simulated delay for
 * a real fetch. The hook contract stays the same.
 */
export function useCreateVehicle() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createVehicle(input: CreateVehicleInput): Promise<void> {
    setIsLoading(true);
    setError(null);
    try {
      // TODO: replace with real call once backend exposes the endpoint
      // const res = await fetch('/api/admin/vehicles', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   credentials: 'include',
      //   body: JSON.stringify({
      //     brand: input.brand,
      //     model: input.model,
      //     year: input.year,
      //     license_plate: input.licensePlate,
      //     color: input.color,
      //     category: input.category,
      //     engine_type: input.engineType,
      //     horsepower: input.horsepower,
      //     seats: input.seats,
      //     trunk_capacity: input.trunkCapacity,
      //     mileage: input.mileage,
      //     daily_base_price: input.dailyBasePrice,
      //     image_url: input.imageUrl,
      //   }),
      // });
      // if (!res.ok) throw new Error('Failed to create vehicle');
      console.info('[placeholder] createVehicle', input);
      await new Promise((resolve) => setTimeout(resolve, 600));
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
