'use client';

import { useEffect, useState } from 'react';
import BookingsList from '@/components/dashboard/BookingList';
import UpcomingReturns from '@/components/dashboard/UpcomingReturns';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { DashboardPageHeader } from '@/components/dashboard/DashboardPageHeader';
import { dashboardMockData } from '@/data/dashboard/dashboardData';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole } from '@/data/dashboard/constants';

export default function DashboardPage() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);
  const [availableCars, setAvailableCars] = useState<number | null>(null);

  useEffect(() => {
    fetch('/api/vehicles?status=available&limit=1', { credentials: 'include' })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.total != null) setAvailableCars(data.total);
      })
      .catch(() => {});
  }, []);

  const statsData = dashboardMockData.map((stat) =>
    stat.name === 'Available Cars' && availableCars !== null
      ? { ...stat, value: String(availableCars), change: '', trend: 'up' as const }
      : stat
  );

  // Customers see only Active Bookings and Available Cars
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

      {isStaff && <QuickActions />}
    </div>
  );
}
