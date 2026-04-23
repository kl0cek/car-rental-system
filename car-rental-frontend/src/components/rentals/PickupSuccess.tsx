'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { SuccessScreen } from '@/components/dashboard/SuccessScreen';
import type { RentalResponse } from '@/types/rental';

interface PickupSuccessProps {
  result: RentalResponse;
}

export function PickupSuccess({ result }: PickupSuccessProps) {
  return (
    <SuccessScreen
      title="Vehicle pickup logged"
      description={
        <>
          Rental ID:{' '}
          <span className="font-mono text-xs font-semibold">{result.id.slice(0, 8)}…</span>
        </>
      }
      actions={
        <>
          <Button asChild>
            <Link href={`/dashboard/rentals/${result.id}/return`}>Process return later</Link>
          </Button>
          <Button variant="outline" asChild>
            <Link href="/dashboard/bookings">Back to bookings</Link>
          </Button>
        </>
      }
    />
  );
}
