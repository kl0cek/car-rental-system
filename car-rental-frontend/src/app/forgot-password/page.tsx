'use client';

import Link from 'next/link';
import { ArrowLeft, Mail } from 'lucide-react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { StatusMessage } from '@/components/auth/StatusMessage';
import { TextField } from '@/components/home/TextField';
import { useForgotPassword } from '@/src/hooks/useForgotPassword';
import { useTranslation } from '@/i18n/useTranslation';

export default function ForgotPasswordPage() {
  const { email, setEmail, isLoading, submitted, error, handleSubmit } = useForgotPassword();
  const { t } = useTranslation();

  return (
    <AuthLayout>
      {submitted ? (
        <StatusMessage
          icon={Mail}
          iconClassName="text-green-600"
          bgClassName="bg-green-500/10"
          title={t('auth.checkEmail')}
          description={t('auth.checkEmailDesc', { email })}
          link={{ href: '/', label: t('auth.backToSignIn'), icon: ArrowLeft }}
        />
      ) : (
        <>
          <div className="space-y-2 text-center lg:text-left">
            <h2 className="text-2xl font-semibold tracking-tight text-foreground">
              {t('auth.forgotTitle')}
            </h2>
            <p className="text-muted-foreground">{t('auth.forgotDesc')}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <ErrorAlert message={error} />

            <TextField
              id="email"
              label={t('auth.email')}
              type="email"
              placeholder={t('auth.emailPlaceholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />

            <AuthSubmitButton
              label={t('auth.sendResetLink')}
              isLoading={isLoading}
              disabled={!email}
            />
          </form>

          <p className="text-center text-sm text-muted-foreground">
            <Link
              href="/"
              className="inline-flex items-center gap-1 text-primary font-medium hover:text-primary/80 transition-colors"
            >
              <ArrowLeft className="w-3 h-3" />
              {t('auth.backToSignIn')}
            </Link>
          </p>
        </>
      )}
    </AuthLayout>
  );
}
