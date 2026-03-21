import BookingsList from '@/components/dashboard/BookingList';
import UpcomingReturns from '@/components/dashboard/UpcomingReturns';
import { StatsGrid } from '@/components/dashboard/StatsGrid';
import { QuickActions } from '@/components/dashboard/QuickActions';
import { DashboardPageHeader } from '@/components/dashboard/DashboardPageHeader';
import { dashboardMockData } from '@/data/dashboard/dashboardData';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <DashboardPageHeader />

      <StatsGrid data={dashboardMockData} />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <BookingsList />
        </div>
        <div>
          <UpcomingReturns />
        </div>
      </div>

      <QuickActions />
    </div>
  );
}
