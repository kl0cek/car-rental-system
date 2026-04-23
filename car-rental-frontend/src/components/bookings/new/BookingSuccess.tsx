'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { SuccessScreen } from '@/components/dashboard/SuccessScreen';
import { formatDate } from '@/lib/formatters';
import type { ReservationApi } from '@/types/booking';

interface BookingSuccessProps {
  reservation: ReservationApi;
}

export function BookingSuccess({ reservation }: BookingSuccessProps) {
  return (
    <SuccessScreen
      title="Reservation confirmed!"
      description="Your booking has been created. We'll send a confirmation email shortly."
      actions={
        <Button asChild>
          <Link href="/dashboard/bookings">View my bookings</Link>
        </Button>
      }
    >
      <Card className="text-left">
        <CardContent className="p-5 space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Reservation ID</span>
            <span className="font-mono text-xs">{reservation.id.slice(0, 8)}…</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Vehicle</span>
            <span className="font-medium">
              {reservation.vehicle.brand} {reservation.vehicle.model}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Period</span>
            <span className="font-medium">
              {formatDate(reservation.start_date)} – {formatDate(reservation.end_date)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Total</span>
            <span className="font-semibold">{Number(reservation.total_price).toFixed(0)} PLN</span>
          </div>
        </CardContent>
      </Card>
    </SuccessScreen>
  );
}
