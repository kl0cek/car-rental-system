import { useState } from 'react';

export interface ProfileUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
  email?: string;
}

export function useUpdateProfile() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function updateProfile(payload: ProfileUpdatePayload): Promise<void> {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/users/me', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to update profile');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update profile';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { updateProfile, isLoading, error };
}
