'use client';

import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';

interface AvailabilityFilterProps {
  availableFrom: string;
  availableTo: string;
  onChange: (updates: { availableFrom?: string; availableTo?: string }) => void;
}

export function AvailabilityFilter({ availableFrom, availableTo, onChange }: AvailabilityFilterProps) {
  const today = new Date().toISOString().split('T')[0];

  return (
    <div className="space-y-2">
      <Label className="text-xs uppercase tracking-wider text-muted-foreground">Availability</Label>
      <div className="space-y-2">
        <div>
          <Label htmlFor="avail-from" className="text-xs text-muted-foreground mb-1 block">
            From
          </Label>
          <Input
            id="avail-from"
            type="date"
            value={availableFrom}
            min={today}
            onChange={(e) => onChange({ availableFrom: e.target.value })}
          />
        </div>
        <div>
          <Label htmlFor="avail-to" className="text-xs text-muted-foreground mb-1 block">
            To
          </Label>
          <Input
            id="avail-to"
            type="date"
            value={availableTo}
            min={availableFrom || today}
            onChange={(e) => onChange({ availableTo: e.target.value })}
          />
        </div>
      </div>
    </div>
  );
}
