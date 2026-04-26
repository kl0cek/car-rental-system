'use client';

import { useState } from 'react';
import { Wrench, CheckCircle2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TableCell, TableRow } from '@/components/ui/table';
import { formatDate } from '@/lib/formatters';
import { useTranslation } from '@/i18n/useTranslation';
import { MaintenanceForm } from './MaintenanceForm';
import type { MaintenanceVehicle } from '@/hooks/useMaintenanceVehicles';
import type { MaintenancePeriod } from '@/hooks/useUpdateVehicleStatus';

interface MaintenanceRowProps {
  vehicle: MaintenanceVehicle;
  loadingId: string | null;
  onSendToMaintenance: (vehicleId: string, period: MaintenancePeriod) => Promise<void>;
  onMarkFixed: (vehicleId: string) => Promise<void>;
}

export function MaintenanceRow({
  vehicle,
  loadingId,
  onSendToMaintenance,
  onMarkFixed,
}: MaintenanceRowProps) {
  const { t } = useTranslation();
  const [formOpen, setFormOpen] = useState(false);

  const isInMaintenance = vehicle.status === 'maintenance';
  const isLoading = loadingId === vehicle.id;

  async function handleSubmit(period: MaintenancePeriod) {
    await onSendToMaintenance(vehicle.id, period);
    setFormOpen(false);
  }

  return (
    <>
      <TableRow>
        <TableCell className="px-5 py-4">
          <p className="font-medium text-foreground">
            {vehicle.brand} {vehicle.model}
          </p>
          <p className="text-xs text-muted-foreground">{vehicle.licensePlate}</p>
        </TableCell>
        <TableCell className="px-5 py-4">
          <Badge variant={isInMaintenance ? 'destructive' : 'secondary'}>
            {isInMaintenance ? t('fleet.tab.maintenance') : t('fleet.tab.available')}
          </Badge>
        </TableCell>
        <TableCell className="px-5 py-4 text-sm text-muted-foreground">
          {vehicle.maintenancePeriod ? (
            <>
              {formatDate(vehicle.maintenancePeriod.startDate)} –{' '}
              {formatDate(vehicle.maintenancePeriod.endDate)}
            </>
          ) : (
            '—'
          )}
        </TableCell>
        <TableCell className="px-5 py-4 text-right">
          {isInMaintenance ? (
            <Button
              variant="outline"
              size="sm"
              disabled={isLoading}
              onClick={() => onMarkFixed(vehicle.id)}
              className="gap-1.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              {t('maintenance.markEnd')}
            </Button>
          ) : (
            <Button
              variant="outline"
              size="sm"
              disabled={isLoading}
              onClick={() => setFormOpen((v) => !v)}
              className="gap-1.5"
            >
              <Wrench className="w-3.5 h-3.5" />
              {t('maintenance.markStart')}
            </Button>
          )}
        </TableCell>
      </TableRow>
      {formOpen && !isInMaintenance && (
        <TableRow>
          <TableCell colSpan={4} className="p-3">
            <MaintenanceForm
              isLoading={isLoading}
              onSubmit={handleSubmit}
              onCancel={() => setFormOpen(false)}
            />
          </TableCell>
        </TableRow>
      )}
    </>
  );
}
