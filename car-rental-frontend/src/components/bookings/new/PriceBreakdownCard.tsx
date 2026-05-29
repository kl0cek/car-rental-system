'use client';

import { Card, CardContent } from '@/components/ui/card';
import { usePriceQuote } from '@/hooks/usePriceQuote';

interface PriceBreakdownCardProps {
  vehicleId: string;
  startDate: string;
  endDate: string;
  fallbackDailyBase: number;
  fallbackCategoryMultiplier: number;
}

function formatPLN(value: string | number): string {
  const n = typeof value === 'string' ? Number(value) : value;
  return `${n.toFixed(2)} PLN`;
}

export function PriceBreakdownCard({
  vehicleId,
  startDate,
  endDate,
  fallbackDailyBase,
  fallbackCategoryMultiplier,
}: PriceBreakdownCardProps) {
  const { quote, isLoading, error } = usePriceQuote(vehicleId, startDate, endDate);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-5 text-sm text-muted-foreground">
          Calculating price…
        </CardContent>
      </Card>
    );
  }

  if (error || !quote) {
    const estimated = fallbackDailyBase * fallbackCategoryMultiplier;
    return (
      <Card>
        <CardContent className="p-5 space-y-2 text-sm">
          <p className="text-muted-foreground">
            Sign in to see your personalised price. Estimated rate:
          </p>
          <p className="font-semibold">{formatPLN(estimated)} / day</p>
        </CardContent>
      </Card>
    );
  }

  const riskValue = Number(quote.risk_adjustment);
  const riskLabel = riskValue >= 0 ? 'Risk surcharge' : 'Loyalty discount';

  return (
    <Card>
      <CardContent className="p-5 space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Base price</span>
          <span>{formatPLN(quote.daily_base_price)} / day</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Category multiplier</span>
          <span>×{Number(quote.category_multiplier).toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Days</span>
          <span>{quote.days}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Subtotal</span>
          <span>{formatPLN(quote.base_subtotal)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">
            {riskLabel} (×{Number(quote.risk_multiplier).toFixed(2)})
          </span>
          <span className={riskValue >= 0 ? 'text-foreground' : 'text-emerald-600'}>
            {riskValue >= 0 ? '+' : ''}
            {formatPLN(quote.risk_adjustment)}
          </span>
        </div>
        <div className="flex justify-between border-t pt-3 text-base font-semibold">
          <span>Total</span>
          <span>{formatPLN(quote.total)}</span>
        </div>
        <p className="text-xs text-muted-foreground">
          {formatPLN(quote.price_per_day)} / day · risk factor derived from your rental history.
        </p>
      </CardContent>
    </Card>
  );
}
