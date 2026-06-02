'use client';

import { useCallback, useState } from 'react';
import { mutate as globalMutate } from 'swr';
import {
  mapReview,
  type CreateReviewPayload,
  type Review,
  type ReviewApi,
} from '@/types/review';

/**
 * Best-effort revalidation of every SWR key that lists reviews when a
 * mutation lands. We don't know which vehicle's list is currently mounted,
 * so we invalidate the prefixes that matter: per-vehicle review pages, the
 * admin moderation list, and the customer's "rentals available to review".
 */
function revalidateReviewLists(): void {
  globalMutate(
    (key) =>
      typeof key === 'string' &&
      (key.startsWith('/api/vehicles/') && key.includes('/reviews') ||
        key.startsWith('/api/reviews') ||
        key.startsWith('/api/users/me/rentals'))
  );
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: string | { msg?: string }[] };
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
    // fall through
  }
  return `Request failed (${res.status})`;
}

export function useCreateReview(): {
  submit: (payload: CreateReviewPayload) => Promise<Review>;
  isSubmitting: boolean;
  error: string | null;
} {
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (payload: CreateReviewPayload) => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch('/api/reviews', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rental_id: payload.rentalId,
          rating: payload.rating,
          comment: payload.comment,
        }),
      });
      if (!res.ok) {
        const message = await readError(res);
        setError(message);
        throw new Error(message);
      }
      const api = (await res.json()) as ReviewApi;
      revalidateReviewLists();
      return mapReview(api);
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { submit, isSubmitting, error };
}

export function useDeleteReview(): {
  submit: (id: string) => Promise<void>;
  isSubmitting: boolean;
  error: string | null;
} {
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (id: string) => {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/reviews/${id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) {
        const message = await readError(res);
        setError(message);
        throw new Error(message);
      }
      revalidateReviewLists();
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { submit, isSubmitting, error };
}
