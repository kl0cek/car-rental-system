import { Check } from 'lucide-react';

interface StepIndicatorProps {
  steps: readonly string[];
  current: number;
}

export function StepIndicator({ steps, current }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-2 mb-8">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        const circleClass = done
          ? 'bg-primary text-primary-foreground'
          : active
            ? 'bg-primary text-primary-foreground ring-2 ring-primary ring-offset-2'
            : 'bg-secondary text-muted-foreground';

        return (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shrink-0 ${circleClass}`}
              aria-current={active ? 'step' : undefined}
            >
              {done ? <Check className="w-3.5 h-3.5" /> : i + 1}
            </div>
            <span
              className={`text-sm font-medium hidden sm:inline ${active ? 'text-foreground' : 'text-muted-foreground'}`}
            >
              {label}
            </span>
            {i < steps.length - 1 && <div className="w-8 h-px bg-border mx-1" />}
          </div>
        );
      })}
    </div>
  );
}
