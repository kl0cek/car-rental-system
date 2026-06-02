import { useState } from 'react';
import type { RentalResponse } from '@/types/rental';

export interface PickupPayload {
  mileage_start: number;
  fuel_level_start: number;
  photo_urls: string[];
  client_signature_url: string | null;
}

export function usePickupRental() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function pickup(reservationId: string, payload: PickupPayload): Promise<RentalResponse> {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/rentals/${reservationId}/pickup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to process pickup');
      }
      return await res.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process pickup';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { pickup, isLoading, error };
}
