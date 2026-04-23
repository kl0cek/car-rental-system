import { useState } from 'react';

export function useConfirmReservation() {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  async function confirm(id: string): Promise<void> {
    setLoadingId(id);
    try {
      const res = await fetch(`/api/reservations/${id}/confirm`, {
        method: 'PUT',
        credentials: 'include',
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to confirm reservation');
      }
    } finally {
      setLoadingId(null);
    }
  }

  return { confirm, loadingId };
}
