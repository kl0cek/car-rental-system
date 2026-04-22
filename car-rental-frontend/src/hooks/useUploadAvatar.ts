import { useState } from 'react';

export function useUploadAvatar() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function uploadAvatar(file: File): Promise<string> {
    setIsLoading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/users/me/avatar', {
        method: 'POST',
        credentials: 'include',
        body: form,
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail ?? 'Failed to upload avatar');
      }
      const data = await res.json();
      return data.avatar_url as string;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to upload avatar';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }

  return { uploadAvatar, isLoading, error };
}
