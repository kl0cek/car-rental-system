'use client';

import { EyeOff, MoreHorizontal, ExternalLink } from 'lucide-react';
import type { BookingStatus, ReservationApi } from '@/types/booking';
import { useReservations } from '@/hooks/useReservations';
import { useHiddenRows } from '@/hooks/useHiddenRows';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

const statusVariant: Record<BookingStatus, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  active: 'default',
  confirmed: 'secondary',
  pending: 'outline',
  completed: 'secondary',
  cancelled: 'destructive',
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export default function BookingsList() {
  const { reservations, isLoading } = useReservations(5);
  const { hide, showAll, isHidden, hiddenCount } = useHiddenRows();

  const visible = reservations.filter((r) => !isHidden(r.id));

  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Bookings</CardTitle>
            <CardDescription className="mt-0.5">Your recent rental reservations</CardDescription>
          </div>
          <Button
            variant="link"
            className="text-sm p-0 h-auto"
            onClick={hiddenCount > 0 ? showAll : undefined}
          >
            {hiddenCount > 0 ? `View all (${hiddenCount} hidden)` : 'View all'}
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : reservations.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground text-center">No reservations yet.</p>
        ) : (
          <>
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    {['Vehicle', 'Duration', 'Status', 'Total', 'Actions'].map((col) => (
                      <TableHead
                        key={col}
                        className={`text-xs uppercase tracking-wider text-muted-foreground px-5 py-3 ${col === 'Actions' ? 'text-right' : ''}`}
                      >
                        {col}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visible.map((r: ReservationApi) => (
                    <TableRow key={r.id}>
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
                        <Badge variant={statusVariant[r.status]} className="capitalize">
                          {r.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="px-5 py-4 font-medium">
                        {Number(r.total_price).toFixed(0)} PLN
                      </TableCell>
                      <TableCell className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            aria-label="Hide row"
                            onClick={() => hide(r.id)}
                          >
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
                  ))}
                  {visible.length === 0 && (
                    <TableRow>
                      <TableCell
                        colSpan={5}
                        className="text-center text-sm text-muted-foreground py-6"
                      >
                        All rows hidden.{' '}
                        <button onClick={showAll} className="underline">
                          Show all
                        </button>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="md:hidden divide-y divide-border">
              {visible.map((r: ReservationApi) => (
                <div key={r.id} className="p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-foreground">
                        {r.vehicle.brand} {r.vehicle.model}
                      </p>
                      <p className="text-sm text-muted-foreground">{r.vehicle.license_plate}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Badge variant={statusVariant[r.status]} className="capitalize">
                        {r.status}
                      </Badge>
                      <Button variant="ghost" size="icon" onClick={() => hide(r.id)}>
                        <EyeOff className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">
                      {formatDate(r.start_date)} – {formatDate(r.end_date)}
                    </span>
                    <span className="font-medium text-foreground">
                      {Number(r.total_price).toFixed(0)} PLN
                    </span>
                  </div>
                </div>
              ))}
              {visible.length === 0 && (
                <p className="p-4 text-sm text-center text-muted-foreground">
                  All rows hidden.{' '}
                  <button onClick={showAll} className="underline">
                    Show all
                  </button>
                </p>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
