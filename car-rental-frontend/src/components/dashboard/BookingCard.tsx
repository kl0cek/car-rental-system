'use client';

import { EyeOff, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/formatters';
import type { ReservationApi } from '@/types/booking';
import { BOOKING_STATUS_VARIANT } from '@/types/booking';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

const CANCELLABLE_STATUSES = new Set(['pending', 'confirmed']);

interface BookingCardProps {
  reservation: ReservationApi;
  onHide: (id: string) => void;
  onCancel: (id: string) => void;
  cancellingId: string | null;
}

export function BookingCard({ reservation: r, onHide, onCancel, cancellingId }: BookingCardProps) {
  const isCancelling = cancellingId === r.id;
  const canCancel = CANCELLABLE_STATUSES.has(r.status);
  const { t } = useTranslation();

  return (
    <div className="p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium text-foreground">
            {r.vehicle.brand} {r.vehicle.model}
          </p>
          <p className="text-sm text-muted-foreground">{r.vehicle.license_plate}</p>
        </div>
        <div className="flex items-center gap-1">
          <Badge variant={BOOKING_STATUS_VARIANT[r.status]}>
            {t(`status.${r.status}` as TranslationKey)}
          </Badge>
          <Button variant="ghost" size="icon" onClick={() => onHide(r.id)}>
            <EyeOff className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {formatDate(r.start_date)} – {formatDate(r.end_date)}
        </span>
        <span className="font-medium text-foreground">{Number(r.total_price).toFixed(0)} PLN</span>
      </div>
      {canCancel && (
        <Button
          variant="ghost"
          size="sm"
          className="w-full text-red-600 dark:text-red-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
          disabled={isCancelling}
          onClick={() => onCancel(r.id)}
        >
          <XCircle className="w-3.5 h-3.5 mr-1.5" />
          {isCancelling ? t('bookings.cancelling') : t('bookings.action.cancel')}
        </Button>
      )}
    </div>
  );
}
