export type EngineType = 'petrol' | 'diesel' | 'electric' | 'hybrid';
export type VehicleStatus = 'available' | 'rented' | 'maintenance' | 'out_of_service';
export type CategoryName = 'economy' | 'comfort' | 'premium' | 'suv' | 'van';
export type VehicleColor =
  | 'white'
  | 'black'
  | 'grey'
  | 'silver'
  | 'blue'
  | 'red'
  | 'green'
  | 'yellow'
  | 'orange'
  | 'brown'
  | 'beige'
  | 'other';
export type SortableField =
  | 'brand'
  | 'model'
  | 'year'
  | 'daily_base_price'
  | 'created_at'
  | 'mileage'
  | 'horsepower';

export const PRICE_MIN = 0;
export const PRICE_MAX = 2000;
export const YEAR_MIN = 2000;
export const YEAR_MAX = new Date().getFullYear();
export const PAGE_SIZE = 12;

// --- API types (snake_case) ---

export interface CategoryApi {
  id: string;
  name: CategoryName;
  description: string | null;
  price_multiplier: string;
}

export interface VehicleImageApi {
  id: string;
  url: string;
  position: number;
  is_primary: boolean;
}

export interface VehicleApi {
  id: string;
  brand: string;
  model: string;
  year: number;
  license_plate: string;
  engine_type: EngineType;
  horsepower: number;
  seats: number;
  trunk_capacity: number;
  daily_base_price: string;
  color: VehicleColor;
  mileage: number;
  image_url: string | null;
  images: VehicleImageApi[];
  status: VehicleStatus;
  category: CategoryApi;
}

export interface PaginatedVehiclesApi {
  items: VehicleApi[];
  total: number;
  offset: number;
  limit: number;
}

export interface BookedDateRangeApi {
  start_date: string;
  end_date: string;
}

export interface VehicleDetailApi extends VehicleApi {
  vin: string;
  is_active: boolean;
  average_rating: number | null;
  review_count: number;
  booked_dates: BookedDateRangeApi[];
  created_at: string;
  updated_at: string;
}

// --- Frontend types (camelCase) ---

export interface VehicleImage {
  id: string;
  url: string;
  position: number;
  isPrimary: boolean;
}

export interface Vehicle {
  id: string;
  brand: string;
  model: string;
  year: number;
  licensePlate: string;
  engineType: EngineType;
  horsepower: number;
  seats: number;
  trunkCapacity: number;
  dailyBasePrice: number;
  color: VehicleColor;
  mileage: number;
  imageUrl: string | null;
  images: VehicleImage[];
  status: VehicleStatus;
  category: {
    id: string;
    name: CategoryName;
    description: string | null;
    priceMultiplier: number;
  };
}

export interface BookedDateRange {
  startDate: string;
  endDate: string;
}

export interface VehicleDetail extends Vehicle {
  vin: string;
  isActive: boolean;
  averageRating: number | null;
  reviewCount: number;
  bookedDates: BookedDateRange[];
  createdAt: string;
  updatedAt: string;
}

export function mapVehicleImage(api: VehicleImageApi): VehicleImage {
  return {
    id: api.id,
    url: api.url,
    position: api.position,
    isPrimary: api.is_primary,
  };
}

export function mapVehicle(api: VehicleApi): Vehicle {
  return {
    id: api.id,
    brand: api.brand,
    model: api.model,
    year: api.year,
    licensePlate: api.license_plate,
    engineType: api.engine_type,
    horsepower: api.horsepower,
    seats: api.seats,
    trunkCapacity: api.trunk_capacity,
    dailyBasePrice: parseFloat(api.daily_base_price),
    color: api.color,
    mileage: api.mileage,
    imageUrl: api.image_url,
    images: (api.images ?? []).map(mapVehicleImage),
    status: api.status,
    category: {
      id: api.category.id,
      name: api.category.name,
      description: api.category.description,
      priceMultiplier: parseFloat(api.category.price_multiplier),
    },
  };
}

export function mapVehicleDetail(api: VehicleDetailApi): VehicleDetail {
  const base = mapVehicle(api);
  return {
    ...base,
    vin: api.vin,
    isActive: api.is_active,
    averageRating: api.average_rating,
    reviewCount: api.review_count,
    bookedDates: api.booked_dates.map((d) => ({ startDate: d.start_date, endDate: d.end_date })),
    createdAt: api.created_at,
    updatedAt: api.updated_at,
  };
}
