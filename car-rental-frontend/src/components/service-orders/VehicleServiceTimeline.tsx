'use client';

import { Clock, Wrench } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from '@/i18n/useTranslation';
import { useVehicleServiceTimeline } from '@/hooks/service-orders/useVehicleServiceTimeline';
import { ServiceOrderStatusBadge } from './ServiceOrderStatusBadge';
import type { ServiceType } from '@/types/serviceOrder';
import type { TranslationKey } from '@/i18n/translations';

const TYPE_KEYS: Record<ServiceType, TranslationKey> = {
  inspection: 'serviceOrders.type.inspection',
  repair: 'serviceOrders.type.repair',
  tire_swap: 'serviceOrders.type.tireSwap',
  wash: 'serviceOrders.type.wash',
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatCost(value: number | null): string {
  if (value === null) return '—';
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'PLN' }).format(value);
}

export function VehicleServiceTimeline({ vehicleId }: { vehicleId: string }) {
  const { t } = useTranslation();
  const { orders, isLoading } = useVehicleServiceTimeline(vehicleId);

  return (
    <Card>
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Wrench className="w-4 h-4" />
          {t('serviceOrders.timeline.title')}
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : orders.length === 0 ? (
          <p className="p-6 text-sm text-center text-muted-foreground">
            {t('serviceOrders.timeline.empty')}
          </p>
        ) : (
          <ol className="relative ml-6 pr-6 py-4 border-l border-border space-y-5">
            {orders.map((o) => (
              <li key={o.id} className="relative pl-5">
                <span className="absolute -left-[7px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-background" />
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span className="text-sm font-medium">{t(TYPE_KEYS[o.type])}</span>
                  <ServiceOrderStatusBadge status={o.status} />
                  <span className="text-xs text-muted-foreground flex items-center gap-1 ml-auto">
                    <Clock className="w-3 h-3" />
                    {formatDateTime(o.scheduledDate)}
                  </span>
                </div>
                <p className="text-sm text-foreground/90">{o.description}</p>
                <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                  <span>
                    {t('serviceOrders.col.technician')}: {o.technician.firstName}{' '}
                    {o.technician.lastName}
                  </span>
                  <span>
                    {t('serviceOrders.col.cost')}: {formatCost(o.cost)}
                  </span>
                  {o.completedDate && (
                    <span>
                      {t('serviceOrders.timeline.completedAt')}: {formatDateTime(o.completedDate)}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  );
}
