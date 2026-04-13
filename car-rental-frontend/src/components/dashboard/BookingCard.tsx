import { EyeOff } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDate } from '@/lib/formatters';
import type { ReservationApi } from '@/types/booking';
import { BOOKING_STATUS_VARIANT } from '@/types/booking';

interface BookingCardProps {
  reservation: ReservationApi;
  onHide: (id: string) => void;
}

export function BookingCard({ reservation: r, onHide }: BookingCardProps) {
  return (
    <div className="p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium text-foreground">
            {r.vehicle.brand} {r.vehicle.model}
          </p>
          <p className="text-sm text-muted-foreground">{r.vehicle.license_plate}</p>
        </div>
        <div className="flex items-center gap-1">
          <Badge variant={BOOKING_STATUS_VARIANT[r.status]} className="capitalize">
            {r.status}
          </Badge>
          <Button variant="ghost" size="icon" onClick={() => onHide(r.id)}>
            <EyeOff className="w-3.5 h-3.5" />
          </Button>
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          {formatDate(r.start_date)} – {formatDate(r.end_date)}
        </span>
        <span className="font-medium text-foreground">{Number(r.total_price).toFixed(0)} PLN</span>
      </div>
    </div>
  );
}
