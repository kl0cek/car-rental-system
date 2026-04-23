import Link from 'next/link';
import { useAdminReservations } from '@/src/hooks/useAdminReservations';
import { useConfirmReservation } from '@/src/hooks/useConfirmReservation';
import { Badge } from '@/src/components/ui/badge';
import { Button } from '@/src/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/src/components/ui/table';
import { formatDate } from '@/src/lib/formatters';
import { BOOKING_STATUS_VARIANT } from '@/src/types/booking';
import type { BookingStatus } from '@/src/types/booking';
import type { AdminReservationItem } from '@/src/types/rental';
import { LoadingSkeleton } from '@/src/components/LoadingSkeleton';
import { EmptyState } from '@/src/components/EmptyState';
import { CheckCircle, Truck } from 'lucide-react';

export function StaffBookingsTable() {
  const { reservations, isLoading, mutate } = useAdminReservations();
  const { confirm, loadingId: confirmingId } = useConfirmReservation();

  async function handleConfirm(id: string) {
    try {
      await confirm(id);
      await mutate();
    } catch {}
  }

  if (isLoading) return <LoadingSkeleton />;
  if (reservations.length === 0) return <EmptyState />;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {['Customer', 'Vehicle', 'Dates', 'Status', 'Total', 'Actions'].map((col) => (
            <TableHead
              key={col}
              className={`px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground ${col === 'Actions' ? 'text-right' : ''}`}
            >
              {col}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {reservations.map((r: AdminReservationItem) => (
          <TableRow key={r.id}>
            <TableCell className="px-5 py-4">
              <p className="font-medium text-foreground">
                {r.user.first_name} {r.user.last_name}
              </p>
              <p className="text-xs text-muted-foreground">{r.user.email}</p>
            </TableCell>
            <TableCell className="px-5 py-4">
              <p className="font-medium text-foreground">
                {r.vehicle.brand} {r.vehicle.model}
              </p>
              <p className="text-xs text-muted-foreground">{r.vehicle.license_plate}</p>
            </TableCell>
            <TableCell className="px-5 py-4 text-sm">
              <p>{formatDate(r.start_date)}</p>
              <p className="text-muted-foreground">to {formatDate(r.end_date)}</p>
            </TableCell>
            <TableCell className="px-5 py-4">
              <Badge
                variant={BOOKING_STATUS_VARIANT[r.status as BookingStatus] ?? 'outline'}
                className="capitalize"
              >
                {r.status}
              </Badge>
            </TableCell>
            <TableCell className="px-5 py-4 font-medium">
              {Number(r.total_price).toFixed(0)} PLN
            </TableCell>
            <TableCell className="px-5 py-4 text-right">
              <div className="flex items-center justify-end gap-2">
                {r.status === 'pending' && (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={confirmingId === r.id}
                    onClick={() => handleConfirm(r.id)}
                    className="gap-1.5"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    {confirmingId === r.id ? 'Confirming…' : 'Confirm'}
                  </Button>
                )}
                {r.status === 'confirmed' && (
                  <Button variant="outline" size="sm" asChild className="gap-1.5">
                    <Link href={`/dashboard/bookings/${r.id}/pickup`}>
                      <Truck className="w-3.5 h-3.5" />
                      Pickup
                    </Link>
                  </Button>
                )}
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
