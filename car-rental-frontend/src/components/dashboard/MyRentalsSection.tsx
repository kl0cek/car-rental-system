'use client';

import { Car } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate } from '@/lib/formatters';
import { useMyRentals } from '@/hooks/useMyRentals';
import { BOOKING_STATUS_VARIANT } from '@/types/booking';
import type { BookingStatus } from '@/types/booking';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

export function MyRentalsSection() {
  const { rentals, isLoading } = useMyRentals(5);
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <CardTitle>{t('dashboard.myRentals')}</CardTitle>
        <CardDescription className="mt-0.5">{t('dashboard.myRentalsDesc')}</CardDescription>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-14 w-full rounded-lg" />
            ))}
          </div>
        ) : rentals.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-3">
              <Car className="w-6 h-6 text-muted-foreground" />
            </div>
            <p className="text-sm font-medium text-foreground">{t('dashboard.noRentals')}</p>
            <p className="text-xs text-muted-foreground mt-1">{t('dashboard.noRentalsDesc')}</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {rentals.map((r) => (
              <li key={r.id} className="flex items-center justify-between px-5 py-4 gap-4">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-9 h-9 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                    <Car className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-foreground truncate">
                      {r.vehicle.brand} {r.vehicle.model}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(r.pickup_date)}
                      {r.return_date
                        ? ` – ${formatDate(r.return_date)}`
                        : ` · ${t('dashboard.inProgress')}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <Badge variant={BOOKING_STATUS_VARIANT[r.status as BookingStatus] ?? 'outline'}>
                    {t(`status.${r.status}` as TranslationKey)}
                  </Badge>
                  <span className="text-sm font-medium text-foreground">
                    {r.final_price
                      ? `${Number(r.final_price).toFixed(0)} PLN`
                      : `~${Number(r.total_price).toFixed(0)} PLN`}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
