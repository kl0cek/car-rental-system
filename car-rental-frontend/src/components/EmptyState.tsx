'use client';

import { useTranslation } from '@/i18n/useTranslation';

export function EmptyState() {
  const { t } = useTranslation();
  return (
    <div className="py-16 text-center">
      <p className="text-sm font-medium text-foreground">{t('empty.bookings')}</p>
      <p className="text-xs text-muted-foreground mt-1">{t('empty.bookingsDesc')}</p>
    </div>
  );
}
