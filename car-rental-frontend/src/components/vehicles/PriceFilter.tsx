'use client';

import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { useRangeSlider } from '@/hooks/useRangeSlider';
import { PRICE_MIN, PRICE_MAX } from '@/types/vehicle';

interface PriceRangeFilterProps {
  value: [number, number];
  onChange: (value: [number, number]) => void;
}

export function PriceRangeFilter({ value, onChange }: PriceRangeFilterProps) {
  const [local, setLocal] = useRangeSlider(value);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <Label className="text-xs uppercase tracking-wider text-muted-foreground">
          Price / day
        </Label>
        <span className="text-xs text-muted-foreground">
          {local[0]} – {local[1]} PLN
        </span>
      </div>
      <Slider
        min={PRICE_MIN}
        max={PRICE_MAX}
        step={50}
        value={local}
        onValueChange={(v) => setLocal(v as [number, number])}
        onValueCommit={(v) => onChange(v as [number, number])}
      />
    </div>
  );
}
