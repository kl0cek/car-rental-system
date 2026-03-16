import type { Metadata } from 'next';
import { BrandingSidebar } from '@/src/components/home/BrandingSidebar';
import { RegisterForm } from '../../components/register/RegisterForm';

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
