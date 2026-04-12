'use client';

import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { SORT_OPTIONS } from '@/data/vehicles/constants';
import type { SortableField } from '@/types/vehicle';

interface SortSelectProps {
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
  onChange: (sortBy: SortableField, sortOrder: 'asc' | 'desc') => void;
}

export function SortSelect({ sortBy, sortOrder, onChange }: SortSelectProps) {
  const value = `${sortBy}|${sortOrder}`;

  const handleChange = (v: string) => {
    const [sortBy, sortOrder] = v.split('|') as [SortableField, 'asc' | 'desc'];
    const option = SORT_OPTIONS.find((o) => o.value === v);
    if (option) {
      onChange(sortBy, sortOrder);
    }
  };

  return (
    <div className="space-y-2">
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Sort by</Label>
      <Select value={value} onValueChange={handleChange}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SORT_OPTIONS.map((opt) => (
            <SelectItem key={opt.value} value={opt.value}>
              {opt.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
