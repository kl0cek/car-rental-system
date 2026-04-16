'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import type { Vehicle } from '@/types/vehicle';
import { CATEGORY_LABELS } from '@/data/vehicles/constants';

interface PriceCalculatorProps {
  vehicle: Vehicle;
  dateFrom: string;
  dateTo: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
}

export function PriceCalculator({
  vehicle,
  dateFrom,
  dateTo,
  onDateFromChange,
  onDateToChange,
}: PriceCalculatorProps) {
  const today = new Date().toISOString().slice(0, 10);

  const days =
    dateFrom && dateTo
      ? Math.max(
          0,
          Math.ceil((new Date(dateTo).getTime() - new Date(dateFrom).getTime()) / 86400000)
        )
      : 0;
  const baseTotal = days * vehicle.dailyBasePrice;
  const finalTotal = baseTotal * vehicle.category.priceMultiplier;

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">
        Kalkulator ceny
      </h3>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <Label htmlFor="detail-date-from" className="text-xs">
            Od
          </Label>
          <Input
            id="detail-date-from"
            type="date"
            min={today}
            value={dateFrom}
            onChange={(e) => {
              onDateFromChange(e.target.value);
              if (dateTo && e.target.value > dateTo) onDateToChange('');
            }}
            className="mt-1"
          />
        </div>
        <div>
          <Label htmlFor="detail-date-to" className="text-xs">
            Do
          </Label>
          <Input
            id="detail-date-to"
            type="date"
            min={dateFrom || today}
            value={dateTo}
            onChange={(e) => onDateToChange(e.target.value)}
            className="mt-1"
          />
        </div>
      </div>

      {days > 0 ? (
        <div className="bg-secondary/50 rounded-xl p-4 space-y-2 text-sm">
          <div className="flex justify-between text-muted-foreground">
            <span>
              {vehicle.dailyBasePrice.toFixed(0)} PLN/dzień × {days} {days === 1 ? 'dzień' : 'dni'}
            </span>
            <span>{baseTotal.toFixed(0)} PLN</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Mnożnik kategorii ({CATEGORY_LABELS[vehicle.category.name]})</span>
            <span>×{vehicle.category.priceMultiplier.toFixed(2)}</span>
          </div>
          <Separator className="my-1" />
          <div className="flex justify-between font-bold text-foreground text-base">
            <span>Łącznie</span>
            <span>{finalTotal.toFixed(0)} PLN</span>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-2">
          Wybierz daty w kalendarzu lub wpisz je ręcznie
        </p>
      )}
    </div>
  );
}
