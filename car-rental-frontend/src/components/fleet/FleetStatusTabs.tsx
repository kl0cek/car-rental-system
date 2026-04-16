import type { VehicleStatus } from '@/types/vehicle';
import { TABS } from '@/data/vehicles/constants';

interface FleetStatusTabsProps {
  value: VehicleStatus | null;
  onChange: (status: VehicleStatus | null) => void;
}

export function FleetStatusTabs({ value, onChange }: FleetStatusTabsProps) {
  return (
    <div className="flex gap-1 flex-wrap">
      {TABS.map((tab) => (
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
          {tab.label}
        </button>
      ))}
    </div>
  );
}
