'use client';

import { useState, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle } from 'lucide-react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { StatusMessage } from '@/components/auth/StatusMessage';
import { PasswordField } from '@/components/home/PasswordField';
import { useResetPassword } from '@/hooks/auth/useResetPassword';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

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
        title="Invalid link"
        description="This password reset link is invalid or has expired."
        link={{ href: '/forgot-password', label: 'Request a new link', icon: ArrowRight }}
      />
    );
  }

  if (status === 'success') {
    return (
      <StatusMessage
        icon={CheckCircle}
        iconClassName="text-green-600"
        bgClassName="bg-green-500/10"
        title="Password reset!"
        description="Your password has been changed successfully."
        link={{ href: '/', label: 'Back to sign in', icon: ArrowLeft }}
      />
    );
  }

  if (status === 'error') {
    return (
      <StatusMessage
        icon={XCircle}
        iconClassName="text-destructive"
        bgClassName="bg-destructive/10"
        title="Link expired"
        description="This reset link has expired. Please request a new one."
        link={{ href: '/forgot-password', label: 'Request a new link', icon: ArrowRight }}
      />
    );
  }

  return (
    <>
      <div className="space-y-2 text-center lg:text-left">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">Set new password</h2>
        <p className="text-muted-foreground">Enter your new password below.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <ErrorAlert message={error} />

        <PasswordField
          id="password"
          label="New Password"
          placeholder="Enter new password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          show={showPassword}
          onToggle={() => setShowPassword((v) => !v)}
          autoComplete="new-password"
        />

        <div className="space-y-2">
          <PasswordField
            id="confirmPassword"
            label="Confirm Password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            show={showConfirmPassword}
            onToggle={() => setShowConfirmPassword((v) => !v)}
            autoComplete="new-password"
          />
          {confirmPassword && !passwordsMatch && (
            <p className="text-xs text-destructive">Passwords do not match</p>
          )}
        </div>

        <AuthSubmitButton label="Reset password" isLoading={isLoading} disabled={isSubmitDisabled} />
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
