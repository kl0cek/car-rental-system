'use client';

import { useState } from 'react';
import { isPasswordValid } from '@/lib/password';

type Status = 'form' | 'success' | 'error';

export function useResetPassword(token: string | null) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<Status>('form');
  const [error, setError] = useState<string | null>(null);

  const passwordsMatch = password === confirmPassword;
  const isSubmitDisabled = isLoading || !isPasswordValid(password) || !passwordsMatch;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isSubmitDisabled || !token) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Something went wrong');
      }

      setStatus('success');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Something went wrong';
      setError(message);
      if (message.toLowerCase().includes('expired') || message.toLowerCase().includes('invalid')) {
        setStatus('error');
      }
    } finally {
      setIsLoading(false);
    }
  }

  return {
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    isLoading,
    isSubmitDisabled,
    passwordsMatch,
    status,
    error,
    handleSubmit,
  };
}
