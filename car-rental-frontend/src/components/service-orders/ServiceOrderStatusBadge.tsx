'use client';

import { cn } from '@/lib/utils';
import { useTranslation } from '@/i18n/useTranslation';
import type { ServiceOrderStatus } from '@/types/serviceOrder';
import type { TranslationKey } from '@/i18n/translations';

const STATUS_STYLES: Record<ServiceOrderStatus, string> = {
  scheduled: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  in_progress: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  completed: 'bg-emerald-500/10 text-emerald-600 border-emerald-500/20',
};

const STATUS_KEYS: Record<ServiceOrderStatus, TranslationKey> = {
  scheduled: 'serviceOrders.status.scheduled',
  in_progress: 'serviceOrders.status.inProgress',
  completed: 'serviceOrders.status.completed',
};

export function ServiceOrderStatusBadge({ status }: { status: ServiceOrderStatus }) {
  const { t } = useTranslation();
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded-md border text-xs font-medium',
        STATUS_STYLES[status],
      )}
    >
      {t(STATUS_KEYS[status])}
    </span>
  );
}
