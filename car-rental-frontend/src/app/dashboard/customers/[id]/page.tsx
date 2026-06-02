'use client';

import { use } from 'react';
import { AlertTriangle, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { CustomerProfileCard } from '@/components/customers/detail/CustomerProfileCard';
import { CustomerStatsCard } from '@/components/customers/detail/CustomerStatsCard';
import { CustomerRentalsList } from '@/components/customers/detail/CustomerRentalsList';
import { CustomerIncidentsPanel } from '@/components/customers/detail/CustomerIncidentsPanel';
import { CustomerNotesPanel } from '@/components/customers/detail/CustomerNotesPanel';
import { useAuth } from '@/contexts/AuthContext';
import { useCustomerDetail } from '@/hooks/customers/useCustomerDetail';
import { isStaffRole } from '@/data/dashboard/constants';
import { useTranslation } from '@/i18n/useTranslation';

interface CustomerDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function CustomerDetailPage({ params }: CustomerDetailPageProps) {
  const { id } = use(params);
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();
  const { detail, isLoading, error, refresh } = useCustomerDetail(id);

  if (authLoading) {
    return <Skeleton className="h-32 w-full rounded-xl" />;
  }
  if (!user || !isStaffRole(user.role)) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-12 w-1/3 rounded-lg" />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Skeleton className="h-48 rounded-xl" />
          <Skeleton className="h-48 rounded-xl lg:col-span-2" />
        </div>
        <Skeleton className="h-72 w-full rounded-xl" />
      </div>
    );
  }

  if (error || !detail) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{error?.message ?? t('customerDetail.notFound')}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" asChild>
          <Link href="/dashboard/customers" aria-label={t('common.back')}>
            <ArrowLeft className="w-4 h-4" />
          </Link>
        </Button>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            {detail.profile.firstName} {detail.profile.lastName}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">{detail.profile.email}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <CustomerProfileCard profile={detail.profile} />
        <div className="lg:col-span-2">
          <CustomerStatsCard stats={detail.stats} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CustomerRentalsList rentals={detail.rentals} />
        <CustomerIncidentsPanel
          customerId={detail.profile.id}
          incidents={detail.incidents}
          rentals={detail.rentals}
          onChanged={refresh}
        />
      </div>

      <CustomerNotesPanel
        customerId={detail.profile.id}
        notes={detail.notes}
        currentUserId={user.id}
        onChanged={refresh}
      />
    </div>
  );
}
