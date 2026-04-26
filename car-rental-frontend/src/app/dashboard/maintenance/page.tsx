'use client';

import { useMemo, useState } from 'react';
import { Wrench, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { useMaintenanceVehicles } from '@/hooks/useMaintenanceVehicles';
import { useUpdateVehicleStatus, type MaintenancePeriod } from '@/hooks/useUpdateVehicleStatus';
import { MaintenanceTable } from '@/components/maintenance/MaintenanceTable';

const ALLOWED_ROLES = new Set(['technician', 'admin']);

export default function MaintenancePage() {
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();
  const { vehicles, isLoading, setOverride } = useMaintenanceVehicles();
  const { updateStatus, loadingId } = useUpdateVehicleStatus();
  const [tab, setTab] = useState<'available' | 'in-service'>('available');

  const { available, inService } = useMemo(() => {
    const available: typeof vehicles = [];
    const inService: typeof vehicles = [];
    for (const v of vehicles) {
      if (v.status === 'maintenance') inService.push(v);
      else if (v.status === 'available' || v.status === 'rented') available.push(v);
    }
    return { available, inService };
  }, [vehicles]);

  if (authLoading) return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  if (!user || !ALLOWED_ROLES.has(user.role)) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  async function handleSendToMaintenance(vehicleId: string, period: MaintenancePeriod) {
    await updateStatus({ vehicleId, status: 'maintenance', period });
    setOverride(vehicleId, 'maintenance', period);
  }

  async function handleMarkFixed(vehicleId: string) {
    await updateStatus({ vehicleId, status: 'available' });
    setOverride(vehicleId, 'available', undefined);
  }

  const tabs: Array<{ id: 'available' | 'in-service'; labelKey: 'maintenance.tab.available' | 'maintenance.tab.inService'; count: number }> = [
    { id: 'available', labelKey: 'maintenance.tab.available', count: available.length },
    { id: 'in-service', labelKey: 'maintenance.tab.inService', count: inService.length },
  ];

  const visible = tab === 'available' ? available : inService;
  const emptyKey = tab === 'available' ? 'maintenance.empty.available' : 'maintenance.empty.inService';

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
          <Wrench className="w-5 h-5 text-foreground" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('maintenance.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{t('maintenance.subtitle')}</p>
        </div>
      </div>

      <Alert>
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('maintenance.unsupported')}</AlertDescription>
      </Alert>

      <div className="flex gap-1 flex-wrap">
        {tabs.map((tabItem) => (
          <button
            key={tabItem.id}
            onClick={() => setTab(tabItem.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
              tab === tabItem.id
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}
          >
            {t(tabItem.labelKey)}{' '}
            <span className="ml-1 text-xs opacity-80">({tabItem.count})</span>
          </button>
        ))}
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle>{t(tab === 'available' ? 'maintenance.tab.available' : 'maintenance.tab.inService')}</CardTitle>
          <CardDescription>{t('maintenance.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <MaintenanceTable
            vehicles={visible}
            isLoading={isLoading}
            emptyMessage={t(emptyKey)}
            loadingId={loadingId}
            onSendToMaintenance={handleSendToMaintenance}
            onMarkFixed={handleMarkFixed}
          />
        </CardContent>
      </Card>
    </div>
  );
}
