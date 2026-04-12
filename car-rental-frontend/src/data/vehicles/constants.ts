import type { CategoryName, EngineType } from '@/src/types/vehicle';
import { Zap, Fuel, Leaf } from 'lucide-react';

export const CATEGORIES: { value: CategoryName; label: string }[] = [
  { value: 'economy', label: 'Economy' },
  { value: 'comfort', label: 'Comfort' },
  { value: 'premium', label: 'Premium' },
  { value: 'suv', label: 'SUV' },
  { value: 'van', label: 'Van' },
];

export const ENGINE_TYPES: { value: EngineType; label: string }[] = [
  { value: 'petrol', label: 'Petrol' },
  { value: 'diesel', label: 'Diesel' },
  { value: 'electric', label: 'Electric' },
  { value: 'hybrid', label: 'Hybrid' },
];

export const SORT_OPTIONS = [
  { value: 'created_at|desc', label: 'Newest first' },
  { value: 'daily_base_price|asc', label: 'Price: Low to High' },
  { value: 'daily_base_price|desc', label: 'Price: High to Low' },
  { value: 'year|desc', label: 'Year: Newest' },
  { value: 'year|asc', label: 'Year: Oldest' },
  { value: 'mileage|asc', label: 'Mileage: Lowest' },
];

export const SEATS_OPTIONS = [
  { value: '0', label: 'Any' },
  { value: '2', label: '2+' },
  { value: '4', label: '4+' },
  { value: '5', label: '5+' },
  { value: '7', label: '7+' },
];

export const STATUS_CONFIG = {
  available: { label: 'Available', className: 'bg-green-500 text-slate-600' },
  rented: { label: 'Rented', className: 'bg-orange-500 text-slate-600' },
  maintenance: { label: 'Maintenance', className: 'bg-yellow-500 text-slate-600' },
  out_of_service: { label: 'Out of Service', className: 'bg-destructive/10 text-destructive' },
} as const;

export const ENGINE_CONFIG = {
  petrol: { label: 'Petrol', Icon: Fuel },
  diesel: { label: 'Diesel', Icon: Fuel },
  electric: { label: 'Electric', Icon: Zap },
  hybrid: { label: 'Hybrid', Icon: Leaf },
} as const;

export const CATEGORY_LABELS = {
  economy: 'Economy',
  comfort: 'Comfort',
  premium: 'Premium',
  suv: 'SUV',
  van: 'Van',
} as const;
