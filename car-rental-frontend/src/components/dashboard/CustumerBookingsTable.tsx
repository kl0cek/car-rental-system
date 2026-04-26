'use client';

import { Button } from '@/components/ui/button';
import { useMyReservations } from '@/src/hooks/useMyReservations';
import { useCancelReservation } from '@/src/hooks/useCancelReservation';
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

const CANCELLABLE = new Set(['pending', 'confirmed']);

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
  const { t } = useTranslation();

  async function handleCancel(id: string) {
    try {
      await cancel(id);
      await mutate();
    } catch {}
  }

  if (isLoading) return <LoadingSkeleton />;
  if (reservations.length === 0) return <EmptyState />;

  return (
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
        {reservations.map((r) => (
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
                  {cancellingId === r.id ? t('bookings.cancelling') : t('bookings.action.cancel')}
                </Button>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
