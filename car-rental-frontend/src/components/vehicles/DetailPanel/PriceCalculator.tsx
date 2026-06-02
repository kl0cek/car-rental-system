'use client';

import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import type { Vehicle } from '@/types/vehicle';
import { CATEGORY_LABELS } from '@/data/vehicles/constants';
import { usePriceQuote } from '@/hooks/bookings/usePriceQuote';

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

  const { quote, isLoading } = usePriceQuote(vehicle.id, dateFrom, dateTo);

  // Fallback when user is not authenticated — show base × category only (no risk).
  const fallbackBaseTotal = days * vehicle.dailyBasePrice;
  const fallbackFinalTotal = fallbackBaseTotal * vehicle.category.priceMultiplier;

  const baseSubtotal = quote ? Number(quote.base_subtotal) : fallbackFinalTotal;
  const total = quote ? Number(quote.total) : fallbackFinalTotal;
  const riskAdjustment = quote ? Number(quote.risk_adjustment) : 0;
  const riskMultiplier = quote ? Number(quote.risk_multiplier) : 1;

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
            <span>{fallbackBaseTotal.toFixed(0)} PLN</span>
          </div>
          <div className="flex justify-between text-muted-foreground">
            <span>Mnożnik kategorii ({CATEGORY_LABELS[vehicle.category.name]})</span>
            <span>×{vehicle.category.priceMultiplier.toFixed(2)}</span>
          </div>
          {quote && (
            <>
              <div className="flex justify-between text-muted-foreground">
                <span>Suma bez ryzyka</span>
                <span>{baseSubtotal.toFixed(2)} PLN</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>
                  {riskAdjustment >= 0 ? 'Dopłata za ryzyko' : 'Rabat lojalnościowy'} (×
                  {riskMultiplier.toFixed(2)})
                </span>
                <span className={riskAdjustment < 0 ? 'text-emerald-600' : undefined}>
                  {riskAdjustment >= 0 ? '+' : ''}
                  {riskAdjustment.toFixed(2)} PLN
                </span>
              </div>
            </>
          )}
          <Separator className="my-1" />
          <div className="flex justify-between font-bold text-foreground text-base">
            <span>Łącznie</span>
            <span>{total.toFixed(2)} PLN</span>
          </div>
          {!quote && !isLoading && (
            <p className="text-xs text-muted-foreground pt-1">
              * Zaloguj się, aby zobaczyć cenę z uwzględnieniem Twojego profilu ryzyka.
            </p>
          )}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground text-center py-2">
          Wybierz daty w kalendarzu lub wpisz je ręcznie
        </p>
      )}
    </div>
  );
}
