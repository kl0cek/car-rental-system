import { useState } from 'react';
import type { RentalResponse } from '@/types/rental';

export interface ReturnPayload {
  mileage_end: number;
  fuel_level_end: number;
  damage_notes: string | null;
  damage_photo_urls: string[];
  extra_charges: number;
}

export function useReturnRental() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function returnRental(rentalId: string, payload: ReturnPayload): Promise<RentalResponse> {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/rentals/${rentalId}/return`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to process return');
      }
      return await res.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process return';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { returnRental, isLoading, error };
}
