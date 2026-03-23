'use client';

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

  // Customers see only Active Bookings and Available Cars
  const statsData = isStaff
    ? dashboardMockData
    : dashboardMockData.filter((s) => s.name === 'Active Bookings' || s.name === 'Available Cars');

  return (
    <div className="space-y-6">
      <DashboardPageHeader />

      <StatsGrid data={statsData} />

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
