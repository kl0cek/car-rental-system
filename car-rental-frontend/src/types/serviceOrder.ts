// Backend exposes service orders as a state machine: SCHEDULED -> IN_PROGRESS
// -> COMPLETED. We mirror that here so the UI can render badges/transitions
// without ad-hoc string comparisons against the API.

export type ServiceType = 'inspection' | 'repair' | 'tire_swap' | 'wash';
export type ServiceOrderStatus = 'scheduled' | 'in_progress' | 'completed';

export const SERVICE_TYPES: ServiceType[] = ['inspection', 'repair', 'tire_swap', 'wash'];
export const SERVICE_ORDER_STATUSES: ServiceOrderStatus[] = [
  'scheduled',
  'in_progress',
  'completed',
];

// --- API types (snake_case) ---

export interface ServiceOrderVehicleApi {
  id: string;
  brand: string;
  model: string;
  year: number;
  license_plate: string;
  mileage: number;
}

export interface ServiceOrderTechnicianApi {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface ServiceHistoryEntryApi {
  id: string;
  notes: string;
  parts_replaced: string[];
  mileage_at_service: number;
  created_at: string;
}

export interface ServiceOrderApi {
  id: string;
  vehicle_id: string;
  type: ServiceType;
  status: ServiceOrderStatus;
  description: string;
  cost: string | null;
  scheduled_date: string;
  completed_date: string | null;
  technician_id: string;
  created_at: string;
  updated_at: string;
  vehicle: ServiceOrderVehicleApi;
  technician: ServiceOrderTechnicianApi;
  history_entries?: ServiceHistoryEntryApi[];
}

export interface PaginatedServiceOrdersApi {
  items: ServiceOrderApi[];
  total: number;
  offset: number;
  limit: number;
}

export interface ServiceOrderStatsApi {
  scheduled: number;
  in_progress: number;
  completed: number;
  total: number;
}

export interface VehicleServiceTimelineApi {
  vehicle_id: string;
  orders: ServiceOrderApi[];
}

// --- Frontend types (camelCase) ---

export interface ServiceOrderVehicle {
  id: string;
  brand: string;
  model: string;
  year: number;
  licensePlate: string;
  mileage: number;
}

export interface ServiceOrderTechnician {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
}

export interface ServiceHistoryEntry {
  id: string;
  notes: string;
  partsReplaced: string[];
  mileageAtService: number;
  createdAt: string;
}

export interface ServiceOrder {
  id: string;
  vehicleId: string;
  type: ServiceType;
  status: ServiceOrderStatus;
  description: string;
  cost: number | null;
  scheduledDate: string;
  completedDate: string | null;
  technicianId: string;
  createdAt: string;
  updatedAt: string;
  vehicle: ServiceOrderVehicle;
  technician: ServiceOrderTechnician;
  historyEntries: ServiceHistoryEntry[];
}

export interface PaginatedServiceOrders {
  items: ServiceOrder[];
  total: number;
  offset: number;
  limit: number;
}

export interface ServiceOrderStats {
  scheduled: number;
  inProgress: number;
  completed: number;
  total: number;
}

export interface CreateServiceOrderPayload {
  vehicleId: string;
  type: ServiceType;
  description: string;
  cost: number | null;
  scheduledDate: string;
  technicianId?: string;
}

export interface UpdateServiceOrderPayload {
  type?: ServiceType;
  description?: string;
  cost?: number | null;
  scheduledDate?: string;
  technicianId?: string;
}

export interface AddServiceHistoryPayload {
  notes: string;
  partsReplaced: string[];
  mileageAtService: number;
}

function mapVehicle(api: ServiceOrderVehicleApi): ServiceOrderVehicle {
  return {
    id: api.id,
    brand: api.brand,
    model: api.model,
    year: api.year,
    licensePlate: api.license_plate,
    mileage: api.mileage,
  };
}

function mapTechnician(api: ServiceOrderTechnicianApi): ServiceOrderTechnician {
  return {
    id: api.id,
    firstName: api.first_name,
    lastName: api.last_name,
    email: api.email,
  };
}

function mapHistoryEntry(api: ServiceHistoryEntryApi): ServiceHistoryEntry {
  return {
    id: api.id,
    notes: api.notes,
    partsReplaced: api.parts_replaced,
    mileageAtService: api.mileage_at_service,
    createdAt: api.created_at,
  };
}

export function mapServiceOrder(api: ServiceOrderApi): ServiceOrder {
  return {
    id: api.id,
    vehicleId: api.vehicle_id,
    type: api.type,
    status: api.status,
    description: api.description,
    cost: api.cost === null ? null : Number(api.cost),
    scheduledDate: api.scheduled_date,
    completedDate: api.completed_date,
    technicianId: api.technician_id,
    createdAt: api.created_at,
    updatedAt: api.updated_at,
    vehicle: mapVehicle(api.vehicle),
    technician: mapTechnician(api.technician),
    historyEntries: (api.history_entries ?? []).map(mapHistoryEntry),
  };
}

export function mapPaginatedServiceOrders(
  api: PaginatedServiceOrdersApi,
): PaginatedServiceOrders {
  return {
    items: api.items.map(mapServiceOrder),
    total: api.total,
    offset: api.offset,
    limit: api.limit,
  };
}

export function mapServiceOrderStats(api: ServiceOrderStatsApi): ServiceOrderStats {
  return {
    scheduled: api.scheduled,
    inProgress: api.in_progress,
    completed: api.completed,
    total: api.total,
  };
}
