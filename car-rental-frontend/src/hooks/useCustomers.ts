import useSWR from 'swr';
import type { Customer, PaginatedAdminUsersApi, AdminUserApiItem } from '@/types/customer';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  });

function mapUser(u: AdminUserApiItem): Customer {
  return {
    id: u.id,
    firstName: u.first_name,
    lastName: u.last_name,
    email: u.email,
    phone: u.phone,
    isVerified: u.is_verified,
    createdAt: u.created_at,
    avatarUrl: u.avatar_url,
  };
}

export function useCustomers(limit = 100) {
  const { data, isLoading, mutate } = useSWR<PaginatedAdminUsersApi>(
    `/api/admin/users?limit=${limit}&offset=0`,
    fetcher
  );

  return {
    customers: data?.items.map(mapUser) ?? [],
    total: data?.total ?? 0,
    isLoading,
    mutate,
  };
}
