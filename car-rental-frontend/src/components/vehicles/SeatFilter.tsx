'use client';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SEATS_OPTIONS } from '@/data/vehicles/constants';

interface MinSeatsFilterProps {
  value: number | null;
  onChange: (value: number | null) => void;
}

export function MinSeatsFilter({ value, onChange }: MinSeatsFilterProps) {
  return (
    <div className="space-y-2">
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Min. Seats</Label>
      <Select
        value={value ? String(value) : '0'}
        onValueChange={(v) => onChange(v === '0' ? null : Number(v))}
      >
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SEATS_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
