'use client';

import type { VehicleStatus } from '@/types/vehicle';
import { TABS } from '@/data/vehicles/constants';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

interface FleetStatusTabsProps {
  value: VehicleStatus | null;
  onChange: (status: VehicleStatus | null) => void;
}

const STATUS_LABEL_KEYS: Record<string, TranslationKey> = {
  All: 'fleet.tab.all',
  Available: 'fleet.tab.available',
  Rented: 'fleet.tab.rented',
  Maintenance: 'fleet.tab.maintenance',
  'Out of Service': 'fleet.tab.retired',
};

export function FleetStatusTabs({ value, onChange }: FleetStatusTabsProps) {
  const { t } = useTranslation();
  return (
    <div className="flex gap-1 flex-wrap">
      {TABS.map((tab) => {
        const labelKey = STATUS_LABEL_KEYS[tab.label];
        const label = labelKey ? t(labelKey) : tab.label;
        return (
          <button
            key={tab.label}
            onClick={() => onChange(tab.value)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
              value === tab.value
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${tab.dot}`} />
            {label}
          </button>
        );
      })}
    </div>
  );
}
