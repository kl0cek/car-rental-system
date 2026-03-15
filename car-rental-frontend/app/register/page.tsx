import type { Metadata } from 'next';
import { BrandingSidebar } from '@/app/_components/BrandingSidebar';
import { RegisterForm } from './_components/RegisterForm';

export const metadata: Metadata = {
  title: 'Create account | DriveEase',
  description: 'Sign up for DriveEase and start renting cars today.',
};

export default function RegisterPage() {
  return (
    <main className="min-h-screen flex">
      <BrandingSidebar />
      <RegisterForm />
    </main>
  );
}
