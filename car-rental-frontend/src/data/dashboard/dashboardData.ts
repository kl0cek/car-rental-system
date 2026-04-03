import { CalendarCheck, Car, Users, TrendingUp } from 'lucide-react';
import type { Stat } from '@/types/dashboard/booking';

export const dashboardMockData: Stat[] = [
  {
    name: 'Active Bookings',
    value: '24',
    change: '+12%',
    trend: 'up',
    icon: CalendarCheck,
  },
  {
    name: 'Available Cars',
    value: '156',
    change: '-3%',
    trend: 'down',
    icon: Car,
  },
  {
    name: 'Total Customers',
    value: '1,429',
    change: '+8%',
    trend: 'up',
    icon: Users,
  },
  {
    name: 'Revenue This Month',
    value: '$48,250',
    change: '+23%',
    trend: 'up',
    icon: TrendingUp,
  },
];
