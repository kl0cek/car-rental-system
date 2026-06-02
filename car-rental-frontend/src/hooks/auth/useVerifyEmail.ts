'use client';

import { useEffect, useState } from 'react';

type Status = 'loading' | 'success' | 'error';

export function useVerifyEmail(token: string | null) {
  const [status, setStatus] = useState<Status>(() => (token ? 'loading' : 'error'));
  const [error, setError] = useState<string | null>(() =>
    token ? null : 'Missing verification token'
  );

  useEffect(() => {
    if (!token) return;

    fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`, {
      credentials: 'include',
    })
      .then(async (res) => {
        if (res.ok) {
          setStatus('success');
        } else {
          const data = await res.json();
          throw new Error(data.detail ?? 'Verification failed');
        }
      })
      .catch((err) => {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Verification failed');
      });
  }, [token]);

  return { status, error };
}
