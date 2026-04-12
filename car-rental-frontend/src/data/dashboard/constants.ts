import { Car, LayoutDashboard, CalendarDays, Users, Settings, HelpCircle, LayoutGrid } from 'lucide-react';
import type { NavItem } from '@/src/types/booking';
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
  { name: 'Vehicles', href: '/dashboard/vehicles', icon: LayoutGrid },
  { name: 'Fleet', href: '/dashboard/fleet', icon: Car, staffOnly: true },
  { name: 'Customers', href: '/dashboard/customers', icon: Users, staffOnly: true },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
];

export const secondaryNavigation: NavItem[] = [
  { name: 'Help Center', href: '#', icon: HelpCircle },
];
