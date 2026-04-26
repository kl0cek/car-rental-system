'use client';

import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useTranslation } from '@/i18n/useTranslation';
import { MaintenanceRow } from './MaintenanceRow';
import type { MaintenanceVehicle } from '@/hooks/useMaintenanceVehicles';
import type { MaintenancePeriod } from '@/hooks/useUpdateVehicleStatus';

interface MaintenanceTableProps {
  vehicles: MaintenanceVehicle[];
  isLoading: boolean;
  emptyMessage: string;
  loadingId: string | null;
  onSendToMaintenance: (vehicleId: string, period: MaintenancePeriod) => Promise<void>;
  onMarkFixed: (vehicleId: string) => Promise<void>;
}

const COLS = ['maintenance.col.vehicle', 'maintenance.col.status', 'maintenance.col.period', 'maintenance.col.actions'] as const;

export function MaintenanceTable({
  vehicles,
  isLoading,
  emptyMessage,
  loadingId,
  onSendToMaintenance,
  onMarkFixed,
}: MaintenanceTableProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (vehicles.length === 0) {
    return <p className="p-6 text-sm text-center text-muted-foreground">{emptyMessage}</p>;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {COLS.map((key) => (
            <TableHead
              key={key}
              className={`px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground ${key === 'maintenance.col.actions' ? 'text-right' : ''}`}
            >
              {t(key)}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((v) => (
          <MaintenanceRow
            key={v.id}
            vehicle={v}
            loadingId={loadingId}
            onSendToMaintenance={onSendToMaintenance}
            onMarkFixed={onMarkFixed}
          />
        ))}
      </TableBody>
    </Table>
  );
}
