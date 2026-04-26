'use client';

import Link from 'next/link';
import { useState } from 'react';
import { BrandingSidebar } from '@/components/home/BrandingSidebar';
import { useRegisterForm } from '@/src/hooks/useRegisterForm';
import { PasswordRequirements } from './PasswordRequirements';
import { SocialButtons } from '@/components/home/SocialButtons';
import { TextField } from '@/components/home/TextField';
import { PasswordField } from '@/components/home/PasswordField';
import { TermsCheckbox } from '@/components/register/TermsCheckbox';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { useTranslation } from '@/i18n/useTranslation';

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
  const { t } = useTranslation();

  return (
    <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-8">
        <div className="lg:hidden flex justify-center mb-8">
          <BrandingSidebar />
        </div>

        <div className="space-y-2 text-center lg:text-left">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            {t('auth.createAccountTitle')}
          </h2>
          <p className="text-muted-foreground">{t('auth.createAccountDesc')}</p>
        </div>

        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          <ErrorAlert message={error} />

          <div className="grid grid-cols-2 gap-4">
            <TextField
              id="firstName"
              label={t('auth.firstName')}
              type="text"
              placeholder={t('auth.firstNamePlaceholder')}
              value={formData.firstName}
              onChange={updateField('firstName')}
              autoComplete="given-name"
            />
            <TextField
              id="lastName"
              label={t('auth.lastName')}
              type="text"
              placeholder={t('auth.lastNamePlaceholder')}
              value={formData.lastName}
              onChange={updateField('lastName')}
              autoComplete="family-name"
            />
          </div>

          <TextField
            id="email"
            label={t('auth.email')}
            type="email"
            placeholder={t('auth.emailPlaceholder')}
            value={formData.email}
            onChange={updateField('email')}
            autoComplete="email"
          />

          <div className="space-y-2">
            <PasswordField
              id="password"
              label={t('auth.password')}
              placeholder={t('auth.passwordCreate')}
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
              label={t('auth.confirmPassword')}
              placeholder={t('auth.confirmPasswordPlaceholder')}
              value={formData.confirmPassword}
              onChange={updateField('confirmPassword')}
              show={showConfirmPassword}
              onToggle={() => setShowConfirmPassword((v) => !v)}
              autoComplete="new-password"
            />
            {formData.confirmPassword && !passwordsMatch && (
              <p className="text-xs text-destructive" role="alert">
                {t('auth.passwordsMismatch')}
              </p>
            )}
          </div>

          <TermsCheckbox />

          <AuthSubmitButton
            label={t('auth.createAccount')}
            isLoading={isLoading}
            disabled={isSubmitDisabled}
          />
        </form>

        <SocialButtons />

        <p className="text-center text-sm text-muted-foreground">
          {t('auth.alreadyAccount')}{' '}
          <Link
            href="/"
            className="text-primary font-medium hover:text-primary/80 transition-colors"
          >
            {t('auth.signIn')}
          </Link>
        </p>
      </div>
    </div>
  );
}
