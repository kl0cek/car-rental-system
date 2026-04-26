import {
  Car,
  LayoutDashboard,
  CalendarDays,
  Users,
  Settings,
  LayoutGrid,
  CalendarCheck,
  Wrench,
  PlusSquare,
} from 'lucide-react';
import type { NavItem, Stat } from '@/types/booking';
import type { UserRole } from '@/types/auth';

export const STAFF_ROLES: UserRole[] = ['employee', 'technician', 'admin'];

export const STATS_BASE: Stat[] = [
  { name: 'dashboard.activeBookings', value: '—', change: '', trend: 'up', icon: CalendarCheck },
  { name: 'dashboard.availableCars', value: '—', change: '', trend: 'up', icon: Car },
];

export function isStaffRole(role?: UserRole): boolean {
  return role ? STAFF_ROLES.includes(role) : false;
}

export function getFilteredNavigation(role?: UserRole): NavItem[] {
  const staff = isStaffRole(role);
  return navigation.filter((item) => {
    if (item.roles && (!role || !item.roles.includes(role))) return false;
    if (item.staffOnly && !staff) return false;
    return true;
  });
}

export const navigation: NavItem[] = [
  { name: 'nav.dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'nav.bookings', href: '/dashboard/bookings', icon: CalendarDays },
  { name: 'nav.vehicles', href: '/dashboard/vehicles', icon: LayoutGrid },
  { name: 'nav.fleet', href: '/dashboard/fleet', icon: Car, staffOnly: true },
  { name: 'nav.customers', href: '/dashboard/customers', icon: Users, staffOnly: true },
  {
    name: 'nav.maintenance',
    href: '/dashboard/maintenance',
    icon: Wrench,
    roles: ['technician', 'admin'],
  },
  {
    name: 'nav.addVehicle',
    href: '/dashboard/admin/vehicles/new',
    icon: PlusSquare,
    roles: ['admin'],
  },
  { name: 'nav.settings', href: '/dashboard/settings', icon: Settings },
];

export const secondaryNavigation: NavItem[] = [];
