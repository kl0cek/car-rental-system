'use client';

import { useMemo, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useMyReservations } from '@/hooks/reservations/useMyReservations';
import { useCancelReservation } from '@/hooks/reservations/useCancelReservation';
import { useMyRentals } from '@/hooks/rentals/useMyRentals';
import { useMyReviewedRentalIds } from '@/hooks/reviews/useMyReviewedRentalIds';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDate } from '@/lib/formatters';
import { Badge } from '@/components/ui/badge';
import { BOOKING_STATUS_VARIANT } from '@/types/booking';
import type { BookingStatus } from '@/types/booking';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';
import { EmptyState } from '@/components/EmptyState';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';
import { ReviewFormModal } from '@/components/reviews/ReviewFormModal';

const CANCELLABLE = new Set(['pending', 'confirmed']);

interface ActiveReview {
  rentalId: string;
  vehicleLabel: string;
}

const COL_KEYS: TranslationKey[] = [
  'bookings.col.vehicle',
  'common.date',
  'bookings.col.status',
  'bookings.col.total',
  'common.actions',
];

export function CustomerBookingsTable() {
  const { reservations, isLoading, mutate } = useMyReservations();
  const { cancel, loadingId: cancellingId } = useCancelReservation();
  // Completed rentals carry the rental_id we need to attach the review to.
  // Reservations don't expose it, so we fetch rentals separately and map by
  // reservation_id.
  const { rentals } = useMyRentals(100, 'completed');
  const { rentalIds: reviewedRentalIds } = useMyReviewedRentalIds();
  const { t } = useTranslation();
  const [activeReview, setActiveReview] = useState<ActiveReview | null>(null);

  const rentalByReservationId = useMemo(() => {
    const map = new Map<string, string>();
    for (const r of rentals) map.set(r.reservation_id, r.id);
    return map;
  }, [rentals]);

  async function handleCancel(id: string) {
    try {
      await cancel(id);
      await mutate();
    } catch {}
  }

  if (isLoading) return <LoadingSkeleton />;
  if (reservations.length === 0) return <EmptyState />;

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            {COL_KEYS.map((key) => (
              <TableHead
                key={key}
                className={`px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground ${key === 'common.actions' ? 'text-right' : ''}`}
              >
                {t(key)}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {reservations.map((r) => {
            const rentalId = rentalByReservationId.get(r.id);
            return (
              <TableRow key={r.id}>
                <TableCell className="px-5 py-4">
                  <p className="font-medium text-foreground">
                    {r.vehicle.brand} {r.vehicle.model}
                  </p>
                  <p className="text-xs text-muted-foreground">{r.vehicle.license_plate}</p>
                </TableCell>
                <TableCell className="px-5 py-4 text-sm">
                  <p>{formatDate(r.start_date)}</p>
                  <p className="text-muted-foreground">
                    {t('common.to').toLowerCase()} {formatDate(r.end_date)}
                  </p>
                </TableCell>
                <TableCell className="px-5 py-4">
                  <Badge variant={BOOKING_STATUS_VARIANT[r.status as BookingStatus] ?? 'outline'}>
                    {t(`status.${r.status}` as TranslationKey)}
                  </Badge>
                </TableCell>
                <TableCell className="px-5 py-4 font-medium">
                  {Number(r.total_price).toFixed(0)} PLN
                </TableCell>
                <TableCell className="px-5 py-4 text-right">
                  {CANCELLABLE.has(r.status) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:text-destructive hover:bg-destructive/10"
                      disabled={cancellingId === r.id}
                      onClick={() => handleCancel(r.id)}
                    >
                      {cancellingId === r.id
                        ? t('bookings.cancelling')
                        : t('bookings.action.cancel')}
                    </Button>
                  )}
                  {r.status === 'completed' && rentalId && !reviewedRentalIds.has(rentalId) && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        setActiveReview({
                          rentalId,
                          vehicleLabel: `${r.vehicle.brand} ${r.vehicle.model}`,
                        })
                      }
                    >
                      {t('reviews.action.write')}
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      {activeReview && (
        <ReviewFormModal
          rentalId={activeReview.rentalId}
          vehicleLabel={activeReview.vehicleLabel}
          onClose={() => setActiveReview(null)}
        />
      )}
    </>
  );
}
