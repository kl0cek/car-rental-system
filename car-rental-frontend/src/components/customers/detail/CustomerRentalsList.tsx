'use client';

import { Car } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/formatters';
import type { CustomerRentalSummary } from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';

interface CustomerRentalsListProps {
  rentals: CustomerRentalSummary[];
}

const STATUS_VARIANTS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  active: 'default',
  confirmed: 'secondary',
  pending: 'outline',
  completed: 'secondary',
  cancelled: 'destructive',
};

export function CustomerRentalsList({ rentals }: CustomerRentalsListProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{t('customerDetail.rentalHistory')}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {rentals.length === 0 ? (
          <div className="py-12 text-center">
            <Car className="w-8 h-8 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">{t('customerDetail.noRentals')}</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {rentals.map((rental) => {
              const variant = STATUS_VARIANTS[rental.status] ?? 'outline';
              const price = rental.finalPrice ?? rental.totalPrice;
              return (
                <li key={rental.id} className="px-5 py-3 flex items-center gap-3">
                  <div className="w-9 h-9 rounded-md bg-muted flex items-center justify-center shrink-0">
                    <Car className="w-4 h-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{rental.vehicleName}</p>
                    <p className="text-xs text-muted-foreground font-mono">
                      {rental.licensePlate}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm">
                      {formatDate(rental.pickupDate)} —{' '}
                      {rental.returnDate ? formatDate(rental.returnDate) : '—'}
                    </p>
                    <div className="flex items-center justify-end gap-2 mt-1">
                      <Badge variant={variant} className="text-xs capitalize">
                        {rental.status}
                      </Badge>
                      <span className="text-xs font-medium">{price.toFixed(0)} PLN</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
