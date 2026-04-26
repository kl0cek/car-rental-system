'use client';

import { useReservations } from '@/hooks/useReservations';
import { useHiddenRows } from '@/hooks/useHiddenRows';
import { useCancelReservation } from '@/hooks/useCancelReservation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { BookingRow } from './BookingRow';
import { BookingCard } from './BookingCard';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

const COL_KEYS: TranslationKey[] = [
  'bookings.col.vehicle',
  'bookings.col.duration',
  'bookings.col.status',
  'bookings.col.total',
  'bookings.col.actions',
];

function AllHiddenMessage({ onShowAll }: { onShowAll: () => void }) {
  const { t } = useTranslation();
  return (
    <p className="py-6 text-sm text-center text-muted-foreground">
      {t('dashboard.allHidden')}{' '}
      <button onClick={onShowAll} className="underline">
        {t('dashboard.showAll')}
      </button>
    </p>
  );
}

export default function BookingsList() {
  const { reservations, isLoading, mutate } = useReservations(5);
  const { hide, showAll, isHidden, hiddenCount } = useHiddenRows();
  const { cancel, loadingId } = useCancelReservation();
  const { t } = useTranslation();

  const visible = reservations.filter((r) => !isHidden(r.id));

  const handleCancel = async (id: string) => {
    try {
      await cancel(id);
      await mutate();
    } catch (err) {
      console.log('Failed to cancel reservation', err);
    }
  };

  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{t('dashboard.recentBookings')}</CardTitle>
            <CardDescription className="mt-0.5">
              {t('dashboard.recentBookingsDesc')}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {hiddenCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground"
                onClick={showAll}
              >
                {t('dashboard.showHidden', { count: hiddenCount })}
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : reservations.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground text-center">
            {t('dashboard.noReservations')}
          </p>
        ) : (
          <>
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    {COL_KEYS.map((key) => (
                      <TableHead
                        key={key}
                        className={`text-xs uppercase tracking-wider text-muted-foreground px-5 py-3 ${key === 'bookings.col.actions' ? 'text-right' : ''}`}
                      >
                        {t(key)}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visible.map((r) => (
                    <BookingRow
                      key={r.id}
                      reservation={r}
                      onHide={hide}
                      onCancel={handleCancel}
                      cancellingId={loadingId}
                    />
                  ))}
                  {visible.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="p-0">
                        <AllHiddenMessage onShowAll={showAll} />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="md:hidden divide-y divide-border">
              {visible.map((r) => (
                <BookingCard
                  key={r.id}
                  reservation={r}
                  onHide={hide}
                  onCancel={handleCancel}
                  cancellingId={loadingId}
                />
              ))}
              {visible.length === 0 && <AllHiddenMessage onShowAll={showAll} />}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
