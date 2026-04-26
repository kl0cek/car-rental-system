'use client';

import { CalendarCheck, Clock, MapPin } from 'lucide-react';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

const actions: Array<{
  labelKey: TranslationKey;
  descKey: TranslationKey;
  icon: typeof CalendarCheck;
}> = [
  {
    labelKey: 'quickAction.schedulePickup',
    descKey: 'quickAction.schedulePickupDesc',
    icon: CalendarCheck,
  },
  { labelKey: 'quickAction.extendRental', descKey: 'quickAction.extendRentalDesc', icon: Clock },
  { labelKey: 'quickAction.trackVehicle', descKey: 'quickAction.trackVehicleDesc', icon: MapPin },
];

export function QuickActions() {
  const { t } = useTranslation();
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {actions.map(({ labelKey, descKey, icon: Icon }) => (
        <button
          key={labelKey}
          className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-primary/50 hover:shadow-sm transition-all text-left"
        >
          <div className="w-12 h-12 rounded-lg bg-secondary flex items-center justify-center">
            <Icon className="w-6 h-6 text-foreground" />
          </div>
          <div>
            <p className="font-medium text-foreground">{t(labelKey)}</p>
            <p className="text-sm text-muted-foreground">{t(descKey)}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
