'use client';

import Link from 'next/link';
import { Plus } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole } from '@/data/dashboard/constants';
import { CustomerBookingsTable } from '@/components/dashboard/CustumerBookingsTable';
import { StaffBookingsTable } from '@/components/dashboard/StaffBookingTable';
import { useTranslation } from '@/i18n/useTranslation';

export default function BookingsPage() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);
  const { t } = useTranslation();

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('bookings.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isStaff ? t('bookings.allReservations') : t('bookings.yourReservations')}
          </p>
        </div>
        {!isStaff && (
          <Button asChild className="gap-2">
            <Link href="/dashboard/bookings/new">
              <Plus className="w-4 h-4" />
              {t('dashboard.newBooking')}
            </Link>
          </Button>
        )}
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle>
            {isStaff ? t('bookings.allReservationsTitle') : t('bookings.myReservations')}
          </CardTitle>
          <CardDescription>
            {isStaff ? t('bookings.staffDesc') : t('bookings.customerDesc')}
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          {isStaff ? <StaffBookingsTable /> : <CustomerBookingsTable />}
        </CardContent>
      </Card>
    </div>
  );
}
