import { Car, LayoutDashboard, CalendarDays, Users, Settings, HelpCircle } from 'lucide-react';
import type { BookingStatus, NavItem } from '@/types/dashboard/booking';
import type { UserRole } from '@/types/auth';

export const STAFF_ROLES: UserRole[] = ['employee', 'technician', 'admin'];

export function isStaffRole(role?: UserRole): boolean {
  return role ? STAFF_ROLES.includes(role) : false;
}

export function getFilteredNavigation(role?: UserRole): NavItem[] {
  const staff = isStaffRole(role);
  return navigation.filter((item) => !item.staffOnly || staff);
}

export const navigation: NavItem[] = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Bookings', href: '/dashboard/bookings', icon: CalendarDays },
  { name: 'Fleet', href: '/dashboard/fleet', icon: Car, staffOnly: true },
  { name: 'Customers', href: '/dashboard/customers', icon: Users, staffOnly: true },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export const secondaryNavigation: NavItem[] = [
  { name: 'Help Center', href: '#', icon: HelpCircle },
];

export const bookingStatusStyles: Record<BookingStatus, string> = {
  active: 'bg-green-500/15 text-green-600',
  pending: 'bg-yellow-500/15 text-yellow-600',
  completed: 'bg-muted text-muted-foreground',
  confirmed: 'bg-primary/15 text-primary',
};
