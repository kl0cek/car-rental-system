import useSWR from 'swr';
import type { CategoryApi, CategoryName } from '@/types/vehicle';

export interface Category {
  id: string;
  name: CategoryName;
  description: string | null;
  priceMultiplier: number;
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((r) => {
    if (!r.ok) throw new Error('Failed to load categories');
    return r.json() as Promise<CategoryApi[]>;
  });

export function useCategories() {
  const { data, isLoading, error } = useSWR('/api/categories', fetcher, {
    revalidateOnFocus: false,
  });

  const categories: Category[] =
    data?.map((c) => ({
      id: c.id,
      name: c.name,
      description: c.description,
      priceMultiplier: parseFloat(c.price_multiplier),
    })) ?? [];

  return { categories, isLoading, error: error as Error | undefined };
}
