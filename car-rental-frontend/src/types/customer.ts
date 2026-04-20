export interface Customer {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  isVerified: boolean;
  createdAt: string;
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
