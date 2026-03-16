'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { RegisterFormData, PasswordRequirement } from '../../../types/register/register';

const INITIAL_FORM_DATA: RegisterFormData = {
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
};

function getPasswordRequirements(password: string): PasswordRequirement[] {
  return [
    { label: 'At least 8 characters', met: password.length >= 8 },
    { label: 'Contains a number', met: /\d/.test(password) },
    { label: 'Contains uppercase letter', met: /[A-Z]/.test(password) },
  ];
}

export function useRegisterForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<RegisterFormData>(INITIAL_FORM_DATA);
  const [isLoading, setIsLoading] = useState(false);

  const passwordRequirements = getPasswordRequirements(formData.password);
  const passwordsMatch = formData.password === formData.confirmPassword;
  const allRequirementsMet = passwordRequirements.every((r) => r.met);
  const isSubmitDisabled = isLoading || !passwordsMatch || !allRequirementsMet;

  function updateField(field: keyof RegisterFormData) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setFormData((prev) => ({ ...prev, [field]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (isSubmitDisabled) return;

    setIsLoading(true);
    try {
      // TODO: Replace with real API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      router.push('/dashboard');
    } catch (error) {
      console.error('Registration failed:', error);
    } finally {
      setIsLoading(false);
    }
  }

  return {
    formData,
    isLoading,
    isSubmitDisabled,
    passwordRequirements,
    passwordsMatch,
    updateField,
    handleSubmit,
  };
}
