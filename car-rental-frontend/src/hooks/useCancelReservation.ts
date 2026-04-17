import { useState } from 'react';

export function useCancelReservation() {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function cancel(reservationId: string): Promise<void> {
    setLoadingId(reservationId);
    try {
      const res = await fetch(`/api/reservations/${reservationId}/cancel`, {
        method: 'PUT',
        credentials: 'include',
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Nie udało się anulować rezerwacji');
      }
    } finally {
      setLoadingId(null);
    }
  }

  return { cancel, loadingId };
}
