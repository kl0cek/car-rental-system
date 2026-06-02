'use client';

import { useState } from 'react';
import { AlertTriangle, MessageSquare } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { usePendingReviews } from '@/hooks/reviews/usePendingReviews';
import { ModerationTable } from '@/components/reviews/ModerationTable';
import { isStaffRole } from '@/data/dashboard/constants';

export default function ReviewsModerationPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();
  const [page, setPage] = useState(1);

  const { data, isLoading, pageSize } = usePendingReviews({ page });
  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  if (authLoading) return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  if (!user || !isStaffRole(user.role)) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
          <MessageSquare className="w-5 h-5 text-foreground" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('moderation.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{t('moderation.subtitle')}</p>
        </div>
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle>{t('moderation.tab.all')}</CardTitle>
          <CardDescription>{t('moderation.subtitle')}</CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <ModerationTable reviews={data?.items ?? []} isLoading={isLoading && !data} />
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            {t('common.previous')}
          </Button>
          <span className="text-sm text-muted-foreground px-2">
            {page} / {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            {t('common.next')}
          </Button>
        </div>
      )}
    </div>
  );
}
