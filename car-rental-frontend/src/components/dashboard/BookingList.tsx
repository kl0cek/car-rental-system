'use client';

import { MoreHorizontal, Eye } from 'lucide-react';
import type { Booking, BookingStatus } from '@/types/dashboard/booking';
import { mockBookings } from '@/data/dashboard/mockBooking';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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
};

interface BookingsListProps {
  bookings?: Booking[];
}

export default function BookingsList({ bookings = mockBookings }: BookingsListProps) {
  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Bookings</CardTitle>
            <CardDescription className="mt-0.5">Manage your rental reservations</CardDescription>
          </div>
          <Button variant="link" className="text-sm p-0 h-auto">
            View all
          </Button>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="hidden md:block">
          <Table>
            <TableHeader>
              <TableRow>
                {['Customer', 'Vehicle', 'Duration', 'Status', 'Total', 'Actions'].map((col) => (
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
              {bookings.map((booking) => (
                <TableRow key={booking.id}>
                  <TableCell className="px-5 py-4">
                    <p className="font-medium text-foreground">{booking.customer}</p>
                    <p className="text-sm text-muted-foreground">{booking.email}</p>
                  </TableCell>
                  <TableCell className="px-5 py-4">
                    <p className="font-medium text-foreground">{booking.car}</p>
                    <p className="text-sm text-muted-foreground">{booking.licensePlate}</p>
                  </TableCell>
                  <TableCell className="px-5 py-4">
                    <p className="text-foreground">{booking.startDate}</p>
                    <p className="text-sm text-muted-foreground">to {booking.endDate}</p>
                  </TableCell>
                  <TableCell className="px-5 py-4">
                    <Badge variant={statusVariant[booking.status]} className="capitalize">
                      {booking.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-5 py-4 font-medium">{booking.total}</TableCell>
                  <TableCell className="px-5 py-4 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`View booking ${booking.id}`}
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`More options for ${booking.id}`}
                      >
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="md:hidden divide-y divide-border">
          {bookings.map((booking) => (
            <div key={booking.id} className="p-4 space-y-3">
              <div className="flex items-start justify-between">
                <div>
                  <p className="font-medium text-foreground">{booking.customer}</p>
                  <p className="text-sm text-muted-foreground">{booking.car}</p>
                </div>
                <Badge variant={statusVariant[booking.status]} className="capitalize">
                  {booking.status}
                </Badge>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {booking.startDate} – {booking.endDate}
                </span>
                <span className="font-medium text-foreground">{booking.total}</span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
