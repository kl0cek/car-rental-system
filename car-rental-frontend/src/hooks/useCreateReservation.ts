import { useState } from 'react';
import type { ReservationApi } from '@/types/booking';

interface CreateReservationPayload {
  vehicle_id: string;
  start_date: string;
  end_date: string;
}

export function useCreateReservation() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function createReservation(payload: CreateReservationPayload): Promise<ReservationApi> {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/reservations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Nie udało się utworzyć rezerwacji');
      }
      return await res.json();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Nie udało się utworzyć rezerwacji';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { createReservation, isLoading, error };
}
