'use client';

import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { useRangeSlider } from '@/hooks/useRangeSlider';
import { YEAR_MIN, YEAR_MAX } from '@/types/vehicle';

interface YearRangeFilterProps {
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

export function YearRangeFilter({ value, onChange }: YearRangeFilterProps) {
  const [local, setLocal] = useRangeSlider(value);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-xs uppercase tracking-wider text-muted-foreground">Year</Label>
        <span className="text-xs text-muted-foreground">
          {local[0]} – {local[1]}
        </span>
      </div>
      <Slider
        min={YEAR_MIN}
        max={YEAR_MAX}
        step={1}
        value={local}
        onValueChange={(v) => setLocal(v as [number, number])}
        onValueCommit={(v) => onChange(v as [number, number])}
      />
    </div>
  );
}
