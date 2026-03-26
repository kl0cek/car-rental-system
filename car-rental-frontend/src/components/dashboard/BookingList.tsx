'use client';

import { MoreHorizontal, Eye } from 'lucide-react';
import type { Booking } from '@/types/dashboard/booking';
import { bookingStatusStyles } from '@/data/dashboard/constants';
import { mockBookings } from '@/data/dashboard/mockBooking';

interface BookingsListProps {
  bookings?: Booking[];
}

export default function BookingsList({ bookings = mockBookings }: BookingsListProps) {
  return (
    <div className="bg-card rounded-xl border border-border">
      <div className="flex items-center justify-between p-5 border-b border-border">
        <div>
          <h2 className="font-semibold text-foreground">Recent Bookings</h2>
          <p className="text-sm text-muted-foreground mt-0.5">Manage your rental reservations</p>
        </div>
        <button className="text-sm text-primary font-medium hover:text-primary/80 transition-colors">
          View all
        </button>
      </div>

      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border">
              {['Customer', 'Vehicle', 'Duration', 'Status', 'Total', 'Actions'].map((col) => (
                <th
                  key={col}
                  className={`text-xs font-medium text-muted-foreground uppercase tracking-wider px-5 py-3 ${
                    col === 'Actions' ? 'text-right' : 'text-left'
                  }`}
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {bookings.map((booking) => (
              <tr key={booking.id} className="hover:bg-secondary/50 transition-colors">
                <td className="px-5 py-4">
                  <p className="font-medium text-foreground">{booking.customer}</p>
                  <p className="text-sm text-muted-foreground">{booking.email}</p>
                </td>
                <td className="px-5 py-4">
                  <p className="font-medium text-foreground">{booking.car}</p>
                  <p className="text-sm text-muted-foreground">{booking.licensePlate}</p>
                </td>
                <td className="px-5 py-4">
                  <p className="sm foreground">{booking.startDate}</p>
                  <p className="text-sm text-muted-foreground">to {booking.endDate}</p>
                </td>
                <td className="px-5 py-4">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${bookingStatusStyles[booking.status]}`}
                  >
                    {booking.status}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <p className="font-medium text-foreground">{booking.total}</p>
                </td>
                <td className="px-5 py-4 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      aria-label={`View booking ${booking.id}`}
                      className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      aria-label={`More options for ${booking.id}`}
                      className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
                    >
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden divide-y divide-border">
        {bookings.map((booking) => (
          <div key={booking.id} className="p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-foreground">{booking.customer}</p>
                <p className="text-sm text-muted-foreground">{booking.car}</p>
              </div>
              <span
                className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium capitalize ${bookingStatusStyles[booking.status]}`}
              >
                {booking.status}
              </span>
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
    </div>
  );
}
