'use client';

import { useState } from 'react';
import { CheckSquare, Loader2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { VehicleStatus } from '@/types/vehicle';
import { STATUS_CONFIG } from '@/data/vehicles/constants';
import { useTranslation } from '@/i18n/useTranslation';

interface FleetBulkActionBarProps {
  selectedCount: number;
  onClear: () => void;
  onApplyStatus: (status: VehicleStatus) => Promise<void>;
  isLoading: boolean;
}

const STATUS_OPTIONS: VehicleStatus[] = ['available', 'rented', 'maintenance', 'out_of_service'];

export function FleetBulkActionBar({
  selectedCount,
  onClear,
  onApplyStatus,
  isLoading,
}: FleetBulkActionBarProps) {
  const { t } = useTranslation();
  const [pendingStatus, setPendingStatus] = useState<VehicleStatus | null>(null);

  if (selectedCount === 0) return null;

  const apply = async () => {
    if (!pendingStatus) return;
    await onApplyStatus(pendingStatus);
    setPendingStatus(null);
  };

  return (
    <div className="sticky top-2 z-20 flex items-center gap-3 bg-card border border-border shadow-md rounded-xl px-4 py-2.5">
      <CheckSquare className="w-4 h-4 text-primary" />
      <p className="text-sm font-medium">{t('fleet.bulk.selected', { count: selectedCount })}</p>

      <Select
        value={pendingStatus ?? undefined}
        onValueChange={(v) => setPendingStatus(v as VehicleStatus)}
      >
        <SelectTrigger size="sm" className="min-w-[160px]">
          <SelectValue placeholder={t('fleet.bulk.changeStatus')} />
        </SelectTrigger>
        <SelectContent>
          {STATUS_OPTIONS.map((s) => (
            <SelectItem key={s} value={s}>
              <span className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${STATUS_CONFIG[s].dot}`} />
                {STATUS_CONFIG[s].label}
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button size="sm" onClick={apply} disabled={!pendingStatus || isLoading}>
        {isLoading && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
        {t('fleet.bulk.apply')}
      </Button>

      <Button variant="ghost" size="sm" onClick={onClear} className="ml-auto">
        <X className="w-3.5 h-3.5 mr-1" />
        {t('common.cancel')}
      </Button>
    </div>
  );
}
