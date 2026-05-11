import type { UserRole } from '@/types/auth';

export interface Customer {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  isVerified: boolean;
  createdAt: string;
  avatarUrl: string | null;
}

export interface AdminUserApiItem {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string | null;
  is_verified: boolean;
  created_at: string;
  role: string;
  avatar_url: string | null;
  risk_score: string;
  is_active: boolean;
  last_login_at: string | null;
}

export interface PaginatedAdminUsersApi {
  items: AdminUserApiItem[];
  total: number;
  offset: number;
  limit: number;
}

// ===========================================================================
// Customer detail panel (staff view) — incidents, notes, rental history
// ===========================================================================

export type IncidentType =
  | 'damage'
  | 'late_return'
  | 'traffic_violation'
  | 'complaint'
  | 'other';

export type IncidentSeverity = 'minor' | 'moderate' | 'major';

interface PersonRefApi {
  id: string;
  first_name: string;
  last_name: string;
}

export interface IncidentApi {
  id: string;
  customer_id: string;
  rental_id: string | null;
  type: IncidentType;
  severity: IncidentSeverity;
  title: string;
  description: string;
  cost: string | null;
  reported_by: PersonRefApi;
  created_at: string;
}

export interface CustomerNoteApi {
  id: string;
  customer_id: string;
  body: string;
  author: PersonRefApi;
  created_at: string;
  updated_at: string;
}

export interface CustomerRentalSummaryApi {
  id: string;
  vehicle_name: string;
  license_plate: string;
  pickup_date: string;
  return_date: string | null;
  status: string;
  total_price: string;
  final_price: string | null;
}

export interface CustomerStatsApi {
  total_rentals: number;
  completed_rentals: number;
  cancelled_rentals: number;
  total_spent: string;
  incident_count: number;
}

export interface CustomerProfileApi {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone: string | null;
  avatar_url: string | null;
  risk_score: string;
  is_active: boolean;
  is_verified: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface CustomerDetailApi {
  profile: CustomerProfileApi;
  stats: CustomerStatsApi;
  rentals: CustomerRentalSummaryApi[];
  incidents: IncidentApi[];
  notes: CustomerNoteApi[];
}

export interface PersonRef {
  id: string;
  firstName: string;
  lastName: string;
}

export interface Incident {
  id: string;
  customerId: string;
  rentalId: string | null;
  type: IncidentType;
  severity: IncidentSeverity;
  title: string;
  description: string;
  cost: string | null;
  reportedBy: PersonRef;
  createdAt: string;
}

export interface CustomerNote {
  id: string;
  customerId: string;
  body: string;
  author: PersonRef;
  createdAt: string;
  updatedAt: string;
}

export interface CustomerRentalSummary {
  id: string;
  vehicleName: string;
  licensePlate: string;
  pickupDate: string;
  returnDate: string | null;
  status: string;
  totalPrice: number;
  finalPrice: number | null;
}

export interface CustomerStats {
  totalRentals: number;
  completedRentals: number;
  cancelledRentals: number;
  totalSpent: number;
  incidentCount: number;
}

export interface CustomerProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  phone: string | null;
  avatarUrl: string | null;
  riskScore: number;
  isActive: boolean;
  isVerified: boolean;
  lastLoginAt: string | null;
  createdAt: string;
}

export interface CustomerDetail {
  profile: CustomerProfile;
  stats: CustomerStats;
  rentals: CustomerRentalSummary[];
  incidents: Incident[];
  notes: CustomerNote[];
}

function mapPerson(a: PersonRefApi): PersonRef {
  return { id: a.id, firstName: a.first_name, lastName: a.last_name };
}

export function mapIncident(api: IncidentApi): Incident {
  return {
    id: api.id,
    customerId: api.customer_id,
    rentalId: api.rental_id,
    type: api.type,
    severity: api.severity,
    title: api.title,
    description: api.description,
    cost: api.cost,
    reportedBy: mapPerson(api.reported_by),
    createdAt: api.created_at,
  };
}

export function mapCustomerNote(api: CustomerNoteApi): CustomerNote {
  return {
    id: api.id,
    customerId: api.customer_id,
    body: api.body,
    author: mapPerson(api.author),
    createdAt: api.created_at,
    updatedAt: api.updated_at,
  };
}

export function mapCustomerDetail(api: CustomerDetailApi): CustomerDetail {
  const p = api.profile;
  const s = api.stats;
  return {
    profile: {
      id: p.id,
      email: p.email,
      firstName: p.first_name,
      lastName: p.last_name,
      role: p.role,
      phone: p.phone,
      avatarUrl: p.avatar_url,
      riskScore: parseFloat(p.risk_score),
      isActive: p.is_active,
      isVerified: p.is_verified,
      lastLoginAt: p.last_login_at,
      createdAt: p.created_at,
    },
    stats: {
      totalRentals: s.total_rentals,
      completedRentals: s.completed_rentals,
      cancelledRentals: s.cancelled_rentals,
      totalSpent: parseFloat(s.total_spent),
      incidentCount: s.incident_count,
    },
    rentals: api.rentals.map((r) => ({
      id: r.id,
      vehicleName: r.vehicle_name,
      licensePlate: r.license_plate,
      pickupDate: r.pickup_date,
      returnDate: r.return_date,
      status: r.status,
      totalPrice: parseFloat(r.total_price),
      finalPrice: r.final_price ? parseFloat(r.final_price) : null,
    })),
    incidents: api.incidents.map(mapIncident),
    notes: api.notes.map(mapCustomerNote),
  };
}
