'use client';

import { PlusSquare, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { AddVehicleForm } from '@/components/admin/AddVehicleForm';

export default function AddVehiclePage() {
  const { user, isLoading } = useAuth();
  const { t } = useTranslation();

  if (isLoading) return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  if (!user || user.role !== 'admin') {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
          <PlusSquare className="w-5 h-5 text-foreground" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('addVehicle.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{t('addVehicle.subtitle')}</p>
        </div>
      </div>

      <Alert>
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('addVehicle.unsupported')}</AlertDescription>
      </Alert>

      <AddVehicleForm />
    </div>
  );
}
