'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { SuccessScreen } from '@/components/dashboard/SuccessScreen';
import type { RentalResponse } from '@/types/rental';

interface ReturnSuccessProps {
  result: RentalResponse;
}

export function ReturnSuccess({ result }: ReturnSuccessProps) {
  const finalPrice = result.price_breakdown?.final_price;

  return (
    <SuccessScreen
      title="Vehicle returned successfully"
      description={
        finalPrice ? (
          <>
            Final charge:{' '}
            <span className="font-semibold text-foreground">
              {Number(finalPrice).toFixed(2)} PLN
            </span>
          </>
        ) : null
      }
      actions={
        <Button asChild>
          <Link href="/dashboard/bookings">Back to bookings</Link>
        </Button>
      }
    />
  );
}
