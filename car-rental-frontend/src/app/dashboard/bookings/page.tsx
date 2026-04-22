'use client';

import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole } from '@/data/dashboard/constants';
import { CustomerBookingsTable } from '@/components/dashboard/CustumerBookingsTable';
import { StaffBookingsTable } from '@/components/dashboard/StaffBookingTable';

export default function BookingsPage() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Bookings</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isStaff ? 'All reservations' : 'Your reservations'}
          </p>
        </div>
        {!isStaff && (
          <Button asChild className="gap-2">
            <Link href="/dashboard/bookings/new">
              <Plus className="w-4 h-4" />
              New Booking
            </Link>
          </Button>
        )}
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle>{isStaff ? 'All Reservations' : 'My Reservations'}</CardTitle>
          <CardDescription>
            {isStaff
              ? 'Confirm, process pickup and manage all reservations'
              : 'View and manage your car rental reservations'}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {isStaff ? <StaffBookingsTable /> : <CustomerBookingsTable />}
        </CardContent>
      </Card>
    </div>
  );
}
