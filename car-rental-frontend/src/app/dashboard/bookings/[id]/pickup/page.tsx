'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { PageHeader } from '@/components/dashboard/PageHeader';
import { PickupForm } from '@/components/rentals/PickupForm';
import { PickupSuccess } from '@/components/rentals/PickupSuccess';
import type { RentalResponse } from '@/types/rental';

const BACK_HREF = '/dashboard/bookings';

export default function PickupPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<RentalResponse | null>(null);

  if (result) {
    return (
      <div className="max-w-lg mx-auto space-y-6">
        <PageHeader backHref={BACK_HREF} title="Pickup processed" />
        <PickupSuccess result={result} />
      </div>
    );
  }

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <PageHeader
        backHref={BACK_HREF}
        title="Process Pickup"
        subtitle={
          <>
            Reservation <span className="font-mono text-xs">{id.slice(0, 8)}…</span>
          </>
        }
      />
      <PickupForm reservationId={id} cancelHref={BACK_HREF} onSuccess={setResult} />
    </div>
  );
}
