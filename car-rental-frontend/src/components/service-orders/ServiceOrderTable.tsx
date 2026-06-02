'use client';

import { Loader2, Play, CheckCircle2, Pencil } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { useTranslation } from '@/i18n/useTranslation';
import { useUpdateServiceOrderStatus } from '@/hooks/service-orders/useServiceOrderMutations';
import { ServiceOrderStatusBadge } from './ServiceOrderStatusBadge';
import type { ServiceOrder, ServiceOrderStatus, ServiceType } from '@/types/serviceOrder';
import type { TranslationKey } from '@/i18n/translations';

interface Props {
  orders: ServiceOrder[];
  isLoading: boolean;
  emptyMessage: string;
  onEdit?: (order: ServiceOrder) => void;
}

const TYPE_KEYS: Record<ServiceType, TranslationKey> = {
  inspection: 'serviceOrders.type.inspection',
  repair: 'serviceOrders.type.repair',
  tire_swap: 'serviceOrders.type.tireSwap',
  wash: 'serviceOrders.type.wash',
};

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });
}

function formatCost(value: number | null): string {
  if (value === null) return '—';
  return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'PLN' }).format(value);
}

export function ServiceOrderTable({ orders, isLoading, emptyMessage, onEdit }: Props) {
  const { t } = useTranslation();
  const { submit: updateStatus, isSubmitting } = useUpdateServiceOrderStatus();

  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (orders.length === 0) {
    return <p className="p-6 text-sm text-center text-muted-foreground">{emptyMessage}</p>;
  }

  const handleAdvance = async (order: ServiceOrder, next: ServiceOrderStatus) => {
    try {
      await updateStatus(order.id, next);
    } catch {
      // hook captures error, no-op here
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.vehicle')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.type')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.status')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.scheduled')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.technician')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('serviceOrders.col.cost')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground text-right">
            {t('common.actions')}
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {orders.map((o) => (
          <TableRow key={o.id}>
            <TableCell className="px-5 py-3">
              <div className="font-medium">
                {o.vehicle.brand} {o.vehicle.model}
              </div>
              <div className="text-xs text-muted-foreground">{o.vehicle.licensePlate}</div>
            </TableCell>
            <TableCell className="px-5 py-3 text-sm">{t(TYPE_KEYS[o.type])}</TableCell>
            <TableCell className="px-5 py-3">
              <ServiceOrderStatusBadge status={o.status} />
            </TableCell>
            <TableCell className="px-5 py-3 text-sm">{formatDate(o.scheduledDate)}</TableCell>
            <TableCell className="px-5 py-3 text-sm">
              {o.technician.firstName} {o.technician.lastName}
            </TableCell>
            <TableCell className="px-5 py-3 text-sm tabular-nums">{formatCost(o.cost)}</TableCell>
            <TableCell className="px-5 py-3 text-right">
              <div className="inline-flex items-center gap-1.5">
                {o.status !== 'completed' && onEdit && (
                  <Button variant="outline" size="sm" onClick={() => onEdit(o)}>
                    <Pencil className="w-3.5 h-3.5" />
                    {t('common.edit')}
                  </Button>
                )}
                {o.status === 'scheduled' && (
                  <Button
                    size="sm"
                    onClick={() => handleAdvance(o, 'in_progress')}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5" />
                    )}
                    {t('serviceOrders.action.start')}
                  </Button>
                )}
                {o.status === 'in_progress' && (
                  <Button
                    size="sm"
                    onClick={() => handleAdvance(o, 'completed')}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    {t('serviceOrders.action.complete')}
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
