import { CalendarCheck, Clock, MapPin } from 'lucide-react';

const actions = [
  {
    label: 'Schedule Pickup',
    description: 'Arrange customer pickup',
    icon: CalendarCheck,
    colorClass: 'bg-secondary',
    iconColorClass: 'text-foreground',
  },
  {
    label: 'Extend Rental',
    description: 'Modify booking duration',
    icon: Clock,
    colorClass: 'bg-secondary',
    iconColorClass: 'text-foreground',
  },
  {
    label: 'Track Vehicle',
    description: 'Real-time location',
    icon: MapPin,
    colorClass: 'bg-secondary',
    iconColorClass: 'text-foreground',
  },
];

export function QuickActions() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {actions.map(({ label, description, icon: Icon, colorClass, iconColorClass }) => (
        <button
          key={label}
          className="flex items-center gap-4 p-4 bg-card rounded-xl border border-border hover:border-primary/50 hover:shadow-sm transition-all text-left"
        >
          <div className={`w-12 h-12 rounded-lg ${colorClass} flex items-center justify-center`}>
            <Icon className={`w-6 h-6 ${iconColorClass}`} />
          </div>
          <div>
            <p className="font-medium text-foreground">{label}</p>
            <p className="text-sm text-muted-foreground">{description}</p>
          </div>
        </button>
      ))}
    </div>
  );
}
