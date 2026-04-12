import type { Return } from '@/src/types/booking';

export const mockReturns: Return[] = [
  {
    id: 1,
    customer: 'Sarah Johnson',
    car: 'BMW 3 Series',
    returnTime: 'Today, 2:00 PM',
    location: 'Downtown Office',
    urgent: true,
  },
  {
    id: 2,
    customer: 'Michael Chen',
    car: 'Mercedes C-Class',
    returnTime: 'Today, 5:30 PM',
    location: 'Airport Terminal',
    urgent: false,
  },
  {
    id: 3,
    customer: 'Emily Davis',
    car: 'Audi A4',
    returnTime: 'Tomorrow, 10:00 AM',
    location: 'Main Branch',
    urgent: false,
  },
  {
    id: 4,
    customer: 'Robert Kim',
    car: 'Tesla Model 3',
    returnTime: 'Tomorrow, 3:00 PM',
    location: 'East Side Office',
    urgent: false,
  },
];
