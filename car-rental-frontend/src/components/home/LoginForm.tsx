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

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get('registered') === 'true';
  const { login } = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({ email: '', password: '' });

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
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">Welcome back</h2>
        <p className="text-muted-foreground">Enter your credentials to access your account</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {justRegistered && (
          <div className="p-3 rounded-lg bg-green-500/10 text-green-700 text-sm" role="status">
            Account created successfully! Please check your email to verify your account, then
            sign in.
          </div>
        )}

        <ErrorAlert message={error} />

        <TextField
          id="email"
          label="Email"
          type="email"
          placeholder="name@company.com"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          autoComplete="email"
        />

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-sm font-medium text-foreground">
              Password
            </label>
            <Link
              href="/forgot-password"
              className="text-sm text-primary hover:text-primary/80 transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <PasswordField
            id="password"
            label=""
            placeholder="Enter your password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            show={showPassword}
            onToggle={() => setShowPassword((v) => !v)}
            autoComplete="current-password"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="remember"
            className="w-4 h-4 rounded border-input text-primary focus:ring-ring"
          />
          <label htmlFor="remember" className="text-sm text-muted-foreground">
            Remember me for 30 days
          </label>
        </div>

        <AuthSubmitButton label="Sign in" isLoading={isLoading} />
      </form>

      <SocialButtons />

      <p className="text-center text-sm text-muted-foreground">
        {"Don't have an account? "}
        <Link
          href="/register"
          className="text-primary font-medium hover:text-primary/80 transition-colors"
        >
          Create account
        </Link>
      </p>
    </>
  );
}
