'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { RegisterFormData } from '@/types/register';
import { useAuth } from '@/contexts/AuthContext';
import { getPasswordRequirements, isPasswordValid } from '@/lib/password';

const INITIAL_FORM_DATA: RegisterFormData = {
  firstName: '',
  lastName: '',
  email: '',
  password: '',
  confirmPassword: '',
};

export function useRegisterForm() {
  const router = useRouter();
  const { register } = useAuth();
  const [formData, setFormData] = useState<RegisterFormData>(INITIAL_FORM_DATA);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const passwordRequirements = getPasswordRequirements(formData.password);
  const passwordsMatch = formData.password === formData.confirmPassword;
  const isSubmitDisabled = isLoading || !passwordsMatch || !isPasswordValid(formData.password);

  function updateField(field: keyof RegisterFormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isSubmitDisabled) return;

    setIsLoading(true);
    setError(null);
    try {
      await register({
        firstName: formData.firstName,
        lastName: formData.lastName,
        email: formData.email,
        password: formData.password,
      });
      router.push('/?registered=true');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  }

  return {
    formData,
    isLoading,
    isSubmitDisabled,
    error,
    passwordRequirements,
    passwordsMatch,
    updateField,
    handleSubmit,
  };
}
