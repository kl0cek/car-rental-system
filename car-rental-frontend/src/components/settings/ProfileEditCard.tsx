'use client';

import { useState } from 'react';
import { User, Save } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { SettingsCard } from './SettingsCard';
import { useUpdateProfile } from '@/hooks/useUpdateProfile';
import type { User as UserType } from '@/types/auth';
import { useTranslation } from '@/i18n/useTranslation';

interface ProfileEditCardProps {
  user: UserType | null;
  onUpdated: () => void;
}

export function ProfileEditCard({ user, onUpdated }: ProfileEditCardProps) {
  const [firstName, setFirstName] = useState(user?.firstName ?? '');
  const [lastName, setLastName] = useState(user?.lastName ?? '');
  const [email, setEmail] = useState(user?.email ?? '');
  const [phone, setPhone] = useState('');
  const [success, setSuccess] = useState(false);
  const { updateProfile, isLoading, error } = useUpdateProfile();
  const { t } = useTranslation();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSuccess(false);
    const payload: Record<string, string> = {};
    if (firstName && firstName !== user?.firstName) payload.first_name = firstName;
    if (lastName && lastName !== user?.lastName) payload.last_name = lastName;
    if (email && email !== user?.email) payload.email = email;
    if (phone) payload.phone = phone;
    if (Object.keys(payload).length === 0) return;
    try {
      await updateProfile(payload);
      setSuccess(true);
      onUpdated();
    } catch (err) {
      console.error('Failed to update profile', err);
    }
  }

  return (
    <SettingsCard icon={User} title={t('profile.title')} description={t('profile.description')}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="firstName">{t('profile.firstName')}</Label>
            <Input
              id="firstName"
              value={firstName}
              onChange={(e) => setFirstName(e.target.value)}
              placeholder={t('profile.firstName')}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="lastName">{t('profile.lastName')}</Label>
            <Input
              id="lastName"
              value={lastName}
              onChange={(e) => setLastName(e.target.value)}
              placeholder={t('profile.lastName')}
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">{t('profile.email')}</Label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('profile.emailPlaceholder')}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="phone">{t('profile.phone')}</Label>
          <Input
            id="phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+48 600 100 200"
          />
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
        {success && <p className="text-sm text-green-600">{t('profile.success')}</p>}
        <Button type="submit" disabled={isLoading} className="gap-2">
          <Save className="w-4 h-4" />
          {isLoading ? t('profile.saving') : t('profile.save')}
        </Button>
      </form>
    </SettingsCard>
  );
}
