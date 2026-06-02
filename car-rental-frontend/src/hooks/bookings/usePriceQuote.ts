import useSWR from 'swr';

export interface PriceBreakdown {
  vehicle_id: string;
  start_date: string;
  end_date: string;
  days: number;
  daily_base_price: string;
  category_multiplier: string;
  risk_multiplier: string;
  risk_adjustment: string;
  base_subtotal: string;
  price_per_day: string;
  total: string;
}

const fetcher = async (url: string): Promise<PriceBreakdown> => {
  const res = await fetch(url, { credentials: 'include' });
  if (!res.ok) throw new Error('Failed to fetch price quote');
  return res.json();
};

export function usePriceQuote(vehicleId: string | null, startDate: string, endDate: string) {
  const enabled = !!vehicleId && !!startDate && !!endDate && startDate !== endDate;
  const key = enabled
    ? `/api/pricing/quote?vehicle_id=${vehicleId}&start_date=${startDate}&end_date=${endDate}`
    : null;

  const { data, isLoading, error } = useSWR<PriceBreakdown>(key, fetcher);

  return {
    quote: data ?? null,
    isLoading: enabled && isLoading,
    error,
  };
}
