'use client';

import { Mail, Phone, Calendar, ShieldCheck, ShieldAlert } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate, getInitials } from '@/lib/formatters';
import type { CustomerProfile } from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

interface CustomerProfileCardProps {
  profile: CustomerProfile;
}

function riskTone(score: number): string {
  // < 30 — low (green); 30-60 — medium (yellow); > 60 — high (red)
  if (score >= 60) return 'bg-destructive/10 text-destructive';
  if (score >= 30) return 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-300';
  return 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300';
}

export function CustomerProfileCard({ profile }: CustomerProfileCardProps) {
  const { t } = useTranslation();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{t('customerDetail.profile')}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-secondary overflow-hidden flex items-center justify-center shrink-0">
            {profile.avatarUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={profile.avatarUrl}
                alt={getInitials(profile.firstName, profile.lastName)}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-sm font-semibold text-secondary-foreground">
                {getInitials(profile.firstName, profile.lastName)}
              </span>
            )}
          </div>
          <div>
            <p className="font-medium">
              {profile.firstName} {profile.lastName}
            </p>
            <p className="text-xs text-muted-foreground">
              {t(`role.${profile.role}` as TranslationKey)}
            </p>
          </div>
        </div>

        <div className="space-y-2 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Mail className="w-3.5 h-3.5" />
            <span className="truncate">{profile.email}</span>
          </div>
          {profile.phone && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Phone className="w-3.5 h-3.5" />
              <span>{profile.phone}</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="w-3.5 h-3.5" />
            <span>
              {t('customerDetail.memberSince')} {formatDate(profile.createdAt)}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-border">
          <div className="flex items-center gap-2">
            {profile.isVerified ? (
              <Badge variant="secondary" className="gap-1">
                <ShieldCheck className="w-3 h-3" />
                {t('account.verified')}
              </Badge>
            ) : (
              <Badge variant="outline" className="gap-1 text-muted-foreground">
                <ShieldAlert className="w-3 h-3" />
                {t('account.notVerified')}
              </Badge>
            )}
          </div>
          <Badge className={riskTone(profile.riskScore)}>
            {t('customerDetail.riskScore')}: {profile.riskScore.toFixed(1)}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
}
