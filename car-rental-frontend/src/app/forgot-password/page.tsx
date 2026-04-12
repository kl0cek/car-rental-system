'use client';

import Link from 'next/link';
import { ArrowLeft, Mail } from 'lucide-react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { StatusMessage } from '@/components/auth/StatusMessage';
import { TextField } from '@/components/home/TextField';
import { useForgotPassword } from '@/src/hooks/useForgotPassword';

export default function ForgotPasswordPage() {
  const { email, setEmail, isLoading, submitted, error, handleSubmit } = useForgotPassword();

  return (
    <AuthLayout>
      {submitted ? (
        <StatusMessage
          icon={Mail}
          iconClassName="text-green-600"
          bgClassName="bg-green-500/10"
          title="Check your email"
          description={`If an account with ${email} exists, we've sent a password reset link.`}
          link={{ href: '/', label: 'Back to sign in', icon: ArrowLeft }}
        />
      ) : (
        <>
          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">
              Forgot password?
            </h2>
            <p className="text-muted-foreground">
              Enter your email and we&apos;ll send you a reset link.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <ErrorAlert message={error} />

            <TextField
              id="email"
              label="Email"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />

            <AuthSubmitButton label="Send reset link" isLoading={isLoading} disabled={!email} />
          </form>

          <p className="text-center text-sm text-muted-foreground">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-primary font-medium hover:text-primary/80 transition-colors"
            >
              <ArrowLeft className="w-3 h-3" />
              Back to sign in
            </Link>
          </p>
        </>
      )}
    </AuthLayout>
  );
}
