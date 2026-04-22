'use client';

import { useEffect, useState } from 'react';
import BookingsList from '@/components/dashboard/BookingList';
import UpcomingReturns from '@/components/dashboard/UpcomingReturns';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { DashboardPageHeader } from '@/components/dashboard/DashboardPageHeader';
import { MyRentalsSection } from '@/components/dashboard/MyRentalsSection';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole, STATS_BASE } from '@/data/dashboard/constants';
import type { Stat, PaginatedReservationsApi } from '@/types/booking';
import type { PaginatedVehiclesApi } from '@/types/vehicle';

export default function DashboardPage() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);
  const [availableCars, setAvailableCars] = useState<number | null>(null);
  const [activeBookings, setActiveBookings] = useState<number | null>(null);

  useEffect(() => {
    fetch('/api/vehicles?status=available&limit=1', { credentials: 'include' })
      .then(
        (res): Promise<PaginatedVehiclesApi | null> => (res.ok ? res.json() : Promise.resolve(null))
      )
      .then((data) => {
        if (data?.total != null) setAvailableCars(data.total);
      })
      .catch(() => {});

    fetch('/api/reservations?status=active&limit=1', { credentials: 'include' })
      .then(
        (res): Promise<PaginatedReservationsApi | null> =>
          res.ok ? res.json() : Promise.resolve(null)
      )
      .then((data) => {
        if (data?.total != null) setActiveBookings(data.total);
      })
      .catch(() => {});
  }, []);

  const statsData: Stat[] = STATS_BASE.map((stat) => {
    if (stat.name === 'Active Bookings' && activeBookings !== null)
      return { ...stat, value: String(activeBookings) };
    if (stat.name === 'Available Cars' && availableCars !== null)
      return { ...stat, value: String(availableCars) };
    return stat;
  });

  const filteredStats = isStaff
    ? statsData
    : statsData.filter((s) => s.name === 'Active Bookings' || s.name === 'Available Cars');

  return (
    <div className="space-y-6">
      <DashboardPageHeader />

      <StatsGrid data={filteredStats} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={isStaff ? 'lg:col-span-2' : 'lg:col-span-3'}>
          <BookingsList />
        </div>
        {isStaff && (
          <div>
            <UpcomingReturns />
          </div>
        )}
      </div>

      {!isStaff && <MyRentalsSection />}

      {isStaff && <QuickActions />}
    </div>
  );
}
