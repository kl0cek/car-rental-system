'use client';

import { useRef, useState } from 'react';
import { Camera } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SettingsCard } from './SettingsCard';
import { useUploadAvatar } from '@/hooks/useUploadAvatar';
import { getInitials } from '@/lib/formatters';
import type { User } from '@/types/auth';
import { useTranslation } from '@/i18n/useTranslation';

interface AvatarCardProps {
  user: User | null;
  onUploaded: () => void;
}

export function AvatarCard({ user, onUploaded }: AvatarCardProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const { uploadAvatar, isLoading, error } = useUploadAvatar();
  const { t } = useTranslation();

  async function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setSuccess(false);
    try {
      await uploadAvatar(file);
      setSuccess(true);
      onUploaded();
    } catch {
      setPreview(null);
    }
  }

  const initials = user ? getInitials(user.firstName, user.lastName) : '??';

  return (
    <SettingsCard icon={Camera} title={t('avatar.title')} description={t('avatar.description')}>
      <div className="flex items-center gap-5">
        <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center shrink-0 overflow-hidden">
          {preview ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="Avatar preview" className="w-full h-full object-cover" />
          ) : user?.avatarUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.avatarUrl} alt={initials} className="w-full h-full object-cover" />
          ) : (
            <span className="text-lg font-semibold text-secondary-foreground">{initials}</span>
          )}
        </div>
        <div className="space-y-2">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={handleFile}
          />
          <Button
            type="button"
            variant="outline"
            disabled={isLoading}
            onClick={() => fileRef.current?.click()}
            className="gap-2"
          >
            <Camera className="w-4 h-4" />
            {isLoading ? t('avatar.uploading') : t('avatar.choose')}
          </Button>
          <p className="text-xs text-muted-foreground">{t('avatar.hint')}</p>
          {error && <p className="text-xs text-destructive">{error}</p>}
          {success && <p className="text-xs text-green-600">{t('avatar.success')}</p>}
        </div>
      </div>
    </SettingsCard>
  );
}
