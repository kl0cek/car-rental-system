'use client';

import { use } from 'react';
import { Pencil, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { useVehicleDetail } from '@/hooks/vehicles/useVehicleDetail';
import { EditVehicleForm } from '@/components/admin/EditVehicleForm';

interface EditVehiclePageProps {
  params: Promise<{ id: string }>;
}

export default function EditVehiclePage({ params }: EditVehiclePageProps) {
  const { id } = use(params);
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();
  const { vehicle, isLoading, error, refresh } = useVehicleDetail(id);

  if (authLoading || isLoading) {
    return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  }

  if (!user || user.role !== 'admin') {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  if (error || !vehicle) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{error?.message ?? t('editVehicle.notFound')}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
          <Pencil className="w-5 h-5 text-foreground" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('editVehicle.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {vehicle.brand} {vehicle.model} · {vehicle.licensePlate}
          </p>
        </div>
      </div>

      <EditVehicleForm vehicle={vehicle} onChanged={() => refresh()} />
    </div>
  );
}
