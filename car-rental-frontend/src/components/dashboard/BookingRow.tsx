import { EyeOff, MoreHorizontal, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TableCell, TableRow } from '@/components/ui/table';
import { formatDate } from '@/lib/formatters';
import type { ReservationApi } from '@/types/booking';
import { BOOKING_STATUS_VARIANT } from '@/types/booking';

interface BookingRowProps {
  reservation: ReservationApi;
  onHide: (id: string) => void;
}

export function BookingRow({ reservation: r, onHide }: BookingRowProps) {
  return (
    <TableRow>
      <TableCell className="px-5 py-4">
        <p className="font-medium text-foreground">
          {r.vehicle.brand} {r.vehicle.model}
        </p>
        <p className="text-sm text-muted-foreground">{r.vehicle.license_plate}</p>
      </TableCell>
      <TableCell className="px-5 py-4">
        <p className="text-foreground">{formatDate(r.start_date)}</p>
        <p className="text-sm text-muted-foreground">to {formatDate(r.end_date)}</p>
      </TableCell>
      <TableCell className="px-5 py-4">
        <Badge variant={BOOKING_STATUS_VARIANT[r.status]} className="capitalize">
          {r.status}
        </Badge>
      </TableCell>
      <TableCell className="px-5 py-4 font-medium">
        {Number(r.total_price).toFixed(0)} PLN
      </TableCell>
      <TableCell className="px-5 py-4 text-right">
        <div className="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" aria-label="Hide row" onClick={() => onHide(r.id)}>
            <EyeOff className="w-4 h-4" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="More options">
                <MoreHorizontal className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem disabled>
                <ExternalLink className="w-4 h-4 mr-2" />
                View details
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  );
}
