'use client';

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle } from 'lucide-react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { StatusMessage } from '@/components/auth/StatusMessage';
import { PasswordField } from '@/components/home/PasswordField';
import { useResetPassword } from '@/src/hooks/useResetPassword';
import { useTranslation } from '@/i18n/useTranslation';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');
  const { t } = useTranslation();

  const {
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
  } = useResetPassword(token);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  if (!token) {
    return (
      <StatusMessage
        icon={XCircle}
        iconClassName="text-destructive"
        bgClassName="bg-destructive/10"
        title={t('auth.invalidLink')}
        description={t('auth.invalidLinkDesc')}
        link={{ href: '/forgot-password', label: t('auth.requestNew'), icon: ArrowRight }}
      />
    );
  }

  if (status === 'success') {
    return (
      <StatusMessage
        icon={CheckCircle}
        iconClassName="text-green-600"
        bgClassName="bg-green-500/10"
        title={t('auth.passwordReset')}
        description={t('auth.passwordResetDesc')}
        link={{ href: '/', label: t('auth.backToSignIn'), icon: ArrowLeft }}
      />
    );
  }

  if (status === 'error') {
    return (
      <StatusMessage
        icon={XCircle}
        iconClassName="text-destructive"
        bgClassName="bg-destructive/10"
        title={t('auth.linkExpired')}
        description={t('auth.linkExpiredDesc')}
        link={{ href: '/forgot-password', label: t('auth.requestNew'), icon: ArrowRight }}
      />
    );
  }

  return (
    <>
      <div className="space-y-2 text-center lg:text-left">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('auth.resetTitle')}
        </h2>
        <p className="text-muted-foreground">{t('auth.resetDesc')}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <ErrorAlert message={error} />

        <PasswordField
          id="password"
          label={t('auth.newPassword')}
          placeholder={t('auth.newPasswordPlaceholder')}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          show={showPassword}
          onToggle={() => setShowPassword((v) => !v)}
          autoComplete="new-password"
        />

        <div className="space-y-2">
          <PasswordField
            id="confirmPassword"
            label={t('auth.confirmPassword')}
            placeholder={t('auth.confirmNewPasswordPlaceholder')}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            show={showConfirmPassword}
            onToggle={() => setShowConfirmPassword((v) => !v)}
            autoComplete="new-password"
          />
          {confirmPassword && !passwordsMatch && (
            <p className="text-xs text-destructive">{t('auth.passwordsMismatch')}</p>
          )}
        </div>

        <AuthSubmitButton
          label={t('auth.resetSubmit')}
          isLoading={isLoading}
          disabled={isSubmitDisabled}
        />
      </form>
    </>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<div className="text-foreground">Loading...</div>}>
        <ResetPasswordForm />
      </Suspense>
    </AuthLayout>
  );
}
