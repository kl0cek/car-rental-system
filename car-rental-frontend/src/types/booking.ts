import type { LucideIcon } from 'lucide-react';

export type BookingStatus = 'active' | 'pending' | 'completed' | 'confirmed' | 'cancelled';

export const BOOKING_STATUS_VARIANT: Record<
  BookingStatus,
  'default' | 'secondary' | 'destructive' | 'outline'
> = {
  active: 'default',
  confirmed: 'secondary',
  pending: 'outline',
  completed: 'secondary',
  cancelled: 'destructive',
};

export interface ReservationVehicleApi {
  id: string;
  brand: string;
  model: string;
  year: number;
  license_plate: string;
  image_url: string | null;
}

export interface ReservationApi {
  id: string;
  vehicle_id: string;
  vehicle: ReservationVehicleApi;
  start_date: string;
  end_date: string;
  status: BookingStatus;
  total_price: string;
  created_at: string;
}

export interface PaginatedReservationsApi {
  items: ReservationApi[];
  total: number;
  offset: number;
  limit: number;
}

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
  roles?: import('./auth').UserRole[];
}
