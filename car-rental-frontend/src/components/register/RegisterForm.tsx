'use client';

import Link from 'next/link';
import { useState } from 'react';
import { BrandingSidebar } from '@/components/home/BrandingSidebar';
import { useRegisterForm } from '@/hooks/register/useRegisterForm';
import { PasswordRequirements } from './PasswordRequirements';
import { SocialButtons } from '@/components/home/SocialButtons';
import { TextField } from '@/components/home/TextField';
import { PasswordField } from '@/components/home/PasswordField';
import { TermsCheckbox } from '@/components/register/TermsCheckbox';
import { SubmitButton } from './SubmitButton';

export function RegisterForm() {
  const {
    formData,
    isLoading,
    isSubmitDisabled,
    error,
    passwordRequirements,
    passwordsMatch,
    updateField,
    handleSubmit,
  } = useRegisterForm();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8">
        <div className="lg:hidden flex justify-center mb-8">
          <BrandingSidebar />
        </div>

        <div className="space-y-2 text-center lg:text-left">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            Create an account
          </h2>
          <p className="text-muted-foreground">Fill in your details to get started</p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {error && (
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm" role="alert">
              {error}
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="firstName"
              label="First Name"
              type="text"
              placeholder="John"
              value={formData.firstName}
              onChange={updateField('firstName')}
              autoComplete="given-name"
            />
            <TextField
              id="lastName"
              label="Last Name"
              type="text"
              placeholder="Doe"
              value={formData.lastName}
              onChange={updateField('lastName')}
              autoComplete="family-name"
            />
          </div>

          <TextField
            id="email"
            label="Email"
            type="email"
            placeholder="name@company.com"
            value={formData.email}
            onChange={updateField('email')}
            autoComplete="email"
          />

          <div className="space-y-2">
            <PasswordField
              id="password"
              label="Password"
              placeholder="Create a password"
              value={formData.password}
              onChange={updateField('password')}
              show={showPassword}
              onToggle={() => setShowPassword((v) => !v)}
              autoComplete="new-password"
            />
            {formData.password && <PasswordRequirements requirements={passwordRequirements} />}
          </div>

          <div className="space-y-2">
            <PasswordField
              id="confirmPassword"
              label="Confirm Password"
              placeholder="Confirm your password"
              value={formData.confirmPassword}
              onChange={updateField('confirmPassword')}
              show={showConfirmPassword}
              onToggle={() => setShowConfirmPassword((v) => !v)}
              autoComplete="new-password"
            />
            {formData.confirmPassword && !passwordsMatch && (
              <p className="text-xs text-destructive" role="alert">
                Passwords do not match
              </p>
            )}
          </div>

          <TermsCheckbox />

          <SubmitButton isLoading={isLoading} disabled={isSubmitDisabled} />
        </form>

        <SocialButtons />

        <p className="text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link
            href="/"
            className="text-primary font-medium hover:text-primary/80 transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
