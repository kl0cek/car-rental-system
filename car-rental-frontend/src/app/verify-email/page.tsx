'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { StatusMessage } from '@/components/auth/StatusMessage';
import { useVerifyEmail } from '@/src/hooks/useVerifyEmail';
import { useTranslation } from '@/i18n/useTranslation';

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const { status, error } = useVerifyEmail(searchParams.get('token'));
  const { t } = useTranslation();

  if (status === 'loading') {
    return (
      <div className="text-center space-y-4">
        <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
          <Loader2 className="w-8 h-8 text-primary animate-spin" />
        </div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('auth.verifying')}
        </h2>
        <p className="text-muted-foreground">{t('auth.pleaseWait')}</p>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <StatusMessage
        icon={CheckCircle}
        iconClassName="text-green-600"
        bgClassName="bg-green-500/10"
        title={t('auth.emailVerified')}
        description={t('auth.emailVerifiedDesc')}
        link={{ href: '/', label: t('auth.goToSignIn'), icon: ArrowLeft }}
      />
    );
  }

  return (
    <StatusMessage
      icon={XCircle}
      iconClassName="text-destructive"
      bgClassName="bg-destructive/10"
      title={t('auth.verificationFailed')}
      description={error ?? t('auth.verificationFailedDesc')}
      link={{ href: '/', label: t('auth.backToSignIn'), icon: ArrowLeft }}
    />
  );
}

export default function VerifyEmailPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<div className="text-foreground">Loading...</div>}>
        <VerifyEmailContent />
      </Suspense>
    </AuthLayout>
  );
}
