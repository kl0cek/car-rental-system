'use client';

import { useCallback, useState } from 'react';
import {
  createReview as storeCreate,
  updateReview as storeUpdate,
  deleteReview as storeDelete,
  voteReview as storeVote,
  moderateReview as storeModerate,
} from '@/data/reviews/mockStore';
import {
  mapReview,
  type CreateReviewPayload,
  type UpdateReviewPayload,
  type Review,
  type ModerateReviewPayload,
} from '@/types/review';
import { useAuth } from '@/contexts/AuthContext';

function fakeAsync<T>(value: T): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), 250));
}

export function useCreateReview(): {
  submit: (payload: CreateReviewPayload) => Promise<Review>;
  isSubmitting: boolean;
  error: string | null;
} {
  const { user } = useAuth();
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (payload: CreateReviewPayload) => {
      setSubmitting(true);
      setError(null);
      try {
        const api = storeCreate({
          vehicle_id: payload.vehicleId,
          rental_id: payload.rentalId,
          rating: payload.rating,
          title: payload.title,
          body: payload.body,
          author: {
            id: user?.id ?? 'anonymous',
            first_name: user?.firstName ?? 'Anonim',
            last_name: user?.lastName ?? '',
            avatar_url: user?.avatarUrl ?? null,
          },
        });
        return await fakeAsync(mapReview(api));
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'Failed to create review';
        setError(msg);
        throw e;
      } finally {
        setSubmitting(false);
      }
    },
    [user]
  );

  return { submit, isSubmitting, error };
}

export function useUpdateReview(): {
  submit: (id: string, payload: UpdateReviewPayload) => Promise<Review>;
  isSubmitting: boolean;
  error: string | null;
} {
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (id: string, payload: UpdateReviewPayload) => {
    setSubmitting(true);
    setError(null);
    try {
      const api = storeUpdate({
        id,
        rating: payload.rating,
        title: payload.title,
        body: payload.body,
      });
      return await fakeAsync(mapReview(api));
    } catch (e) {
      const msg = e instanceof Error ? e.message : 'Failed to update review';
      setError(msg);
      throw e;
    } finally {
      setSubmitting(false);
    }
  }, []);

  return { submit, isSubmitting, error };
}

export function useDeleteReview(): {
  submit: (id: string) => Promise<void>;
  isSubmitting: boolean;
} {
  const [isSubmitting, setSubmitting] = useState(false);
  const submit = useCallback(async (id: string) => {
    setSubmitting(true);
    try {
      storeDelete(id);
      await fakeAsync(undefined);
    } finally {
      setSubmitting(false);
    }
  }, []);
  return { submit, isSubmitting };
}

export function useVoteReview(): {
  submit: (id: string, vote: 'helpful' | 'unhelpful' | null) => Promise<void>;
} {
  const submit = useCallback(async (id: string, vote: 'helpful' | 'unhelpful' | null) => {
    storeVote({ id, vote });
    await fakeAsync(undefined);
  }, []);
  return { submit };
}

export function useModerateReview(): {
  submit: (id: string, payload: ModerateReviewPayload) => Promise<void>;
  isSubmitting: boolean;
} {
  const { user } = useAuth();
  const [isSubmitting, setSubmitting] = useState(false);
  const submit = useCallback(
    async (id: string, payload: ModerateReviewPayload) => {
      setSubmitting(true);
      try {
        storeModerate({
          id,
          action: payload.action,
          reason: payload.reason,
          moderatorId: user?.id ?? 'unknown',
        });
        await fakeAsync(undefined);
      } finally {
        setSubmitting(false);
      }
    },
    [user]
  );
  return { submit, isSubmitting };
}
