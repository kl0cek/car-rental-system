'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { useCreateReservation } from '@/hooks/useCreateReservation';
import { formatDate } from '@/lib/formatters';
import type { Vehicle } from '@/types/vehicle';
import type { ReservationApi } from '@/types/booking';
import { SectionHeader } from './SectionHeader';
import { StepNav } from './StepNav';
import { BookingSuccess } from './BookingSuccess';

interface StepConfirmProps {
  startDate: string;
  endDate: string;
  vehicle: Vehicle;
  onBack: () => void;
}

export function StepConfirm({ startDate, endDate, vehicle, onBack }: StepConfirmProps) {
  const { createReservation, isLoading, error } = useCreateReservation();
  const [result, setResult] = useState<ReservationApi | null>(null);

  async function handleConfirm() {
    try {
      const reservation = await createReservation({
        vehicle_id: vehicle.id,
        start_date: startDate,
        end_date: endDate,
      });
      setResult(reservation);
    } catch (err) {
      console.error('Reservation creation failed', err);
    }
  }

  if (result) {
    return <BookingSuccess reservation={result} />;
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Confirm booking"
        description={
          <>
            Review and confirm your reservation for{' '}
            <strong>
              {vehicle.brand} {vehicle.model}
            </strong>
            , {formatDate(startDate)} – {formatDate(endDate)}.
          </>
        }
      />

      <ErrorAlert message={error} />

      <div className="flex justify-between">
        <StepNav onBack={onBack} />
        <Button onClick={handleConfirm} disabled={isLoading} type="button">
          {isLoading ? 'Creating reservation…' : 'Book now'}
        </Button>
      </div>
    </div>
  );
}
