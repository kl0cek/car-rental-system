import type { LucideIcon } from 'lucide-react';

export type BookingStatus = 'active' | 'pending' | 'completed' | 'confirmed';

export interface Booking {
  id: string;
  customer: string;
  email: string;
  car: string;
  licensePlate: string;
  startDate: string;
  endDate: string;
  status: BookingStatus;
  total: string;
}

export interface Return {
  id: number;
  customer: string;
  car: string;
  returnTime: string;
  location: string;
  urgent: boolean;
}

export interface Stat {
  name: string;
  value: string;
  change: string;
  trend: 'up' | 'down';
  icon: LucideIcon;
}

export interface NavItem {
  name: string;
  href: string;
  icon: LucideIcon;
  staffOnly?: boolean;
}
