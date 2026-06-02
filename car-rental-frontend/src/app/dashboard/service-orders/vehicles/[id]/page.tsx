'use client';

import { use } from 'react';
import Link from 'next/link';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { useVehicleDetail } from '@/hooks/vehicles/useVehicleDetail';
import { VehicleServiceTimeline } from '@/components/service-orders/VehicleServiceTimeline';

const ALLOWED_ROLES = new Set(['technician', 'admin']);

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function VehicleServiceTimelinePage({ params }: PageProps) {
  const { id } = use(params);
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();
  const { vehicle, isLoading } = useVehicleDetail(id);

  if (authLoading) return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  if (!user || !ALLOWED_ROLES.has(user.role)) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/dashboard/service-orders">
              <ArrowLeft className="w-4 h-4" />
              {t('common.back')}
            </Link>
          </Button>
          <h1 className="text-2xl font-semibold tracking-tight mt-2">
            {isLoading ? t('common.loading') : `${vehicle?.brand ?? ''} ${vehicle?.model ?? ''}`}
          </h1>
          {vehicle && (
            <p className="text-sm text-muted-foreground mt-0.5">
              {vehicle.licensePlate} · {vehicle.year}
            </p>
          )}
        </div>
      </div>

      <VehicleServiceTimeline vehicleId={id} />
    </div>
  );
}
