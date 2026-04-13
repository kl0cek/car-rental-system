import type { CategoryName, EngineType, SortableField, VehicleStatus } from '@/types/vehicle';
import { Zap, Fuel, Leaf, type LucideIcon } from 'lucide-react';

export const CATEGORIES: { value: CategoryName; label: string }[] = [
  { value: 'economy', label: 'Economy' },
  { value: 'comfort', label: 'Comfort' },
  { value: 'premium', label: 'Premium' },
  { value: 'suv', label: 'SUV' },
  { value: 'van', label: 'Van' },
];

export const CATEGORY_LABELS = Object.fromEntries(
  CATEGORIES.map((c) => [c.value, c.label])
) as Record<CategoryName, string>;

export const ENGINE_TYPES: { value: EngineType; label: string; Icon: LucideIcon }[] = [
  { value: 'petrol', label: 'Petrol', Icon: Fuel },
  { value: 'diesel', label: 'Diesel', Icon: Fuel },
  { value: 'electric', label: 'Electric', Icon: Zap },
  { value: 'hybrid', label: 'Hybrid', Icon: Leaf },
];

export const ENGINE_CONFIG = Object.fromEntries(
  ENGINE_TYPES.map((e) => [e.value, { label: e.label, Icon: e.Icon }])
) as Record<EngineType, { label: string; Icon: LucideIcon }>;

export const STATUS_CONFIG: Record<VehicleStatus, { label: string; className: string; dot: string }> = {
  available:    { label: 'Available',    className: 'bg-green-500 text-slate-600',       dot: 'bg-green-500' },
  rented:       { label: 'Rented',       className: 'bg-orange-500 text-slate-600',      dot: 'bg-orange-500' },
  maintenance:  { label: 'Maintenance',  className: 'bg-yellow-500 text-slate-600',      dot: 'bg-yellow-500' },
  out_of_service: { label: 'Out of Service', className: 'bg-destructive/10 text-destructive', dot: 'bg-destructive' },
};

export const SORT_OPTIONS = [
  { value: 'created_at|desc',       label: 'Newest first' },
  { value: 'daily_base_price|asc',  label: 'Price: Low to High' },
  { value: 'daily_base_price|desc', label: 'Price: High to Low' },
  { value: 'year|desc',             label: 'Year: Newest' },
  { value: 'year|asc',              label: 'Year: Oldest' },
  { value: 'mileage|asc',           label: 'Mileage: Lowest' },
];

export const SEATS_OPTIONS = [
  { value: '0', label: 'Any' },
  { value: '2', label: '2+' },
  { value: '4', label: '4+' },
  { value: '5', label: '5+' },
  { value: '7', label: '7+' },
];

export const TABS: { value: VehicleStatus | null; label: string; dot: string }[] = [
  { value: null, label: 'All', dot: 'bg-muted-foreground' },
  ...Object.entries(STATUS_CONFIG).map(([value, cfg]) => ({
    value: value as VehicleStatus,
    label: cfg.label,
    dot: cfg.dot,
  })),
];

export const SORTABLE_COLS: { label: string; field: SortableField }[] = [
  { label: 'Vehicle',    field: 'brand' },
  { label: 'Year',       field: 'year' },
  { label: 'Mileage',   field: 'mileage' },
  { label: 'Price / day', field: 'daily_base_price' },
];
