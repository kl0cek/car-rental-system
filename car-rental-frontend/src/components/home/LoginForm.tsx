'use client';

import { useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { AuthSubmitButton } from '@/components/auth/AuthSubmitButton';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { SocialButtons } from './SocialButtons';
import { TextField } from './TextField';
import { PasswordField } from './PasswordField';
import { useTranslation } from '@/i18n/useTranslation';

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get('registered') === 'true';
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({ email: '', password: '' });
  const { t } = useTranslation();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      await login(formData.email, formData.password);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="space-y-2 text-center lg:text-left">
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          {t('auth.welcomeBack')}
        </h2>
        <p className="text-muted-foreground">{t('auth.welcomeBackDesc')}</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {justRegistered && (
          <div className="p-3 rounded-lg bg-green-500/10 text-green-700 text-sm" role="status">
            {t('auth.justRegistered')}
          </div>
        )}

        <ErrorAlert message={error} />

        <TextField
          id="email"
          label={t('auth.email')}
          type="email"
          placeholder={t('auth.emailPlaceholder')}
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          autoComplete="email"
        />

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              {t('auth.password')}
            </label>
            <Link
              href="/forgot-password"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              {t('auth.forgotPassword')}
            </Link>
          </div>
          <PasswordField
            id="password"
            label=""
            placeholder={t('auth.passwordPlaceholder')}
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            show={showPassword}
            onToggle={() => setShowPassword((v) => !v)}
            autoComplete="current-password"
          />
        </div>

        <AuthSubmitButton label={t('auth.signIn')} isLoading={isLoading} />
      </form>

      <SocialButtons />

      <p className="text-center text-sm text-muted-foreground">
        {t('auth.noAccount')}{' '}
        <Link
          href="/register"
          className="text-primary font-medium hover:text-primary/80 transition-colors"
        >
          {t('auth.createAccount')}
        </Link>
      </p>
    </>
  );
}
