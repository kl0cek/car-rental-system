import { Label } from '@/components/ui/label';

interface FilterToggleGroupProps<T extends string> {
  label: string;
  options: { value: T; label: string }[];
  value: T | null;
  onChange: (value: T | null) => void;
}

export function FilterToggleGroup<T extends string>({
  label,
  options,
  value,
  onChange,
}: FilterToggleGroupProps<T>) {
  return (
    <div className="space-y-2">
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">{label}</Label>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onChange(value === opt.value ? null : opt.value)}
            className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
              value === opt.value
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border hover:bg-secondary text-foreground'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}
