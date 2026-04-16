export type EngineType = 'petrol' | 'diesel' | 'electric' | 'hybrid';
export type VehicleStatus = 'available' | 'rented' | 'maintenance' | 'out_of_service';
export type CategoryName = 'economy' | 'comfort' | 'premium' | 'suv' | 'van';
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
  color: string;
  mileage: number;
  image_url: string | null;
  status: VehicleStatus;
  category: CategoryApi;
}

export interface PaginatedVehiclesApi {
  items: VehicleApi[];
  total: number;
  offset: number;
  limit: number;
}

// --- Frontend types (camelCase) ---

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
  color: string;
  mileage: number;
  imageUrl: string | null;
  status: VehicleStatus;
  category: {
    id: string;
    name: CategoryName;
    description: string | null;
    priceMultiplier: number;
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
    status: api.status,
    category: {
      id: api.category.id,
      name: api.category.name,
      description: api.category.description,
      priceMultiplier: parseFloat(api.category.price_multiplier),
    },
  };
}
