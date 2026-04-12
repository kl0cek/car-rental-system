import { CalendarCheck, Car } from 'lucide-react';
import type { Stat } from '@/src/types/booking';

export const dashboardMockData: Stat[] = [
  {
    name: 'Active Bookings',
    value: '0',
    change: '',
    trend: 'up',
    icon: CalendarCheck,
  },
  {
    name: 'Available Cars',
    value: '0',
    change: '',
    trend: 'up',
    icon: Car,
  },
];
