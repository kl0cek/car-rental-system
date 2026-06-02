import useSWR from 'swr';

interface MyReviewedRentalsApi {
  rental_ids: string[];
}

const ENDPOINT = '/api/reviews/me/rentals';

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Failed to fetch reviewed rentals (${res.status})`);
    return res.json() as Promise<MyReviewedRentalsApi>;
  });

export function useMyReviewedRentalIds(): {
  rentalIds: Set<string>;
  isLoading: boolean;
} {
  const { data, isLoading } = useSWR(ENDPOINT, fetcher);
  return {
    rentalIds: new Set(data?.rental_ids ?? []),
    isLoading,
  };
}
