export interface UserRentalVehicle {
  id: string;
  brand: string;
  model: string;
  year: number;
  license_plate: string;
  image_url: string | null;
}

export interface UserRentalItem {
  id: string;
  reservation_id: string;
  vehicle: UserRentalVehicle;
  pickup_date: string;
  return_date: string | null;
  status: string;
  total_price: string;
  final_price: string | null;
  created_at: string;
}

export interface PaginatedUserRentalsApi {
  items: UserRentalItem[];
  total: number;
  offset: number;
  limit: number;
}

export interface RentalPriceBreakdown {
  base_price: string;
  fuel_surcharge: string;
  risk_multiplier: string;
  final_price: string;
  calculated_at: string;
}

export interface RentalResponse {
  id: string;
  reservation_id: string;
  pickup_date: string;
  return_date: string | null;
  mileage_start: number;
  mileage_end: number | null;
  fuel_level_start: string;
  fuel_level_end: string | null;
  damage_notes: string | null;
  employee_id: string;
  price_breakdown: RentalPriceBreakdown | null;
  created_at: string;
}

export interface AdminReservationUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AdminReservationVehicle {
  id: string;
  brand: string;
  model: string;
  license_plate: string;
}

export interface AdminReservationItem {
  id: string;
  user: AdminReservationUser;
  vehicle: AdminReservationVehicle;
  start_date: string;
  end_date: string;
  status: string;
  total_price: string;
  created_at: string;
}

export interface PaginatedAdminReservationsApi {
  items: AdminReservationItem[];
  total: number;
  offset: number;
  limit: number;
}
