'use client';

import Link from 'next/link';
import { Plus } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole } from '@/data/dashboard/constants';
import { useTranslation } from '@/i18n/useTranslation';

export function DashboardPageHeader() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);
  const { t } = useTranslation();

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('dashboard.title')}
        </h1>
        <p className="text-muted-foreground mt-1">{t('dashboard.welcome')}</p>
      </div>
      {!isStaff && (
        <Link
          href="/dashboard/bookings/new"
          className="inline-flex items-center justify-center gap-2 h-10 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          {t('dashboard.newBooking')}
        </Link>
      )}
    </div>
  );
}
