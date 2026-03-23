import { Suspense } from 'react';
import { AuthLayout } from '@/components/auth/AuthLayout';
import { LoginForm } from '@/components/home/LoginForm';

export default function LoginPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<div className="text-foreground">Loading...</div>}>
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}
