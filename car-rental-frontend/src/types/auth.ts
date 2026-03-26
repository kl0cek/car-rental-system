export type UserRole = 'customer' | 'employee' | 'technician' | 'admin';

// API DTOs (snake_case - matches backend)
export interface LoginApiRequest {
  email: string;
  password: string;
}

export interface RegisterApiRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone?: string;
}

export interface TokenApiResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserApiResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_verified: boolean;
  created_at: string;
}

// Frontend types (camelCase)
export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  isVerified: boolean;
  createdAt: string;
}

export function mapUserFromApi(apiUser: UserApiResponse): User {
  return {
    id: apiUser.id,
    email: apiUser.email,
    firstName: apiUser.first_name,
    lastName: apiUser.last_name,
    role: apiUser.role,
    isVerified: apiUser.is_verified,
    createdAt: apiUser.created_at,
  };
}
