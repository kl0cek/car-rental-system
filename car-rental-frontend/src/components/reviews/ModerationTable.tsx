'use client';

import { useState } from 'react';
import { Check, Flag, FlagOff, Trash2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate } from '@/lib/formatters';
import { useTranslation } from '@/i18n/useTranslation';
import { useModerateReview } from '@/hooks/useReviewMutations';
import type { Review, ModerationAction } from '@/types/review';
import { StarRating } from './StarRating';

interface ModerationTableProps {
  reviews: Review[];
  isLoading: boolean;
}

function statusBadge(review: Review, t: ReturnType<typeof useTranslation>['t']) {
  if (review.status === 'pending')
    return <Badge variant="outline">{t('reviews.pendingBadge')}</Badge>;
  if (review.status === 'rejected')
    return <Badge variant="destructive">{t('reviews.rejectedBadge')}</Badge>;
  if (review.isFlagged) return <Badge variant="destructive">{t('reviews.flaggedBadge')}</Badge>;
  return <Badge variant="secondary">{t('moderation.tab.approved')}</Badge>;
}

export function ModerationTable({ reviews, isLoading }: ModerationTableProps) {
  const { t } = useTranslation();
  const { submit, isSubmitting } = useModerateReview();
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');

  async function act(id: string, action: ModerationAction, reason?: string) {
    if (action === 'delete' && !window.confirm(t('moderation.confirmDelete'))) return;
    await submit(id, { action, reason });
  }

  async function confirmReject(id: string) {
    await act(id, 'reject', rejectionReason || undefined);
    setRejectingId(null);
    setRejectionReason('');
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    );
  }

  if (reviews.length === 0) {
    return (
      <p className="px-6 py-10 text-center text-sm text-muted-foreground">
        {t('moderation.empty')}
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('moderation.col.review')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('moderation.col.author')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('moderation.col.rating')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('moderation.col.status')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground">
            {t('moderation.col.submitted')}
          </TableHead>
          <TableHead className="px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground text-right">
            {t('moderation.col.actions')}
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {reviews.map((r) => (
          <TableRow key={r.id} className="align-top">
            <TableCell className="px-5 py-4 max-w-md">
              {r.title && <p className="font-medium text-foreground">{r.title}</p>}
              <p className="text-sm text-foreground/90 whitespace-pre-line line-clamp-4">
                {r.body}
              </p>
              {rejectingId === r.id && (
                <div className="mt-2 space-y-2">
                  <textarea
                    autoFocus
                    rows={2}
                    value={rejectionReason}
                    onChange={(e) => setRejectionReason(e.target.value)}
                    placeholder={t('moderation.rejectReasonPlaceholder')}
                    className="w-full text-xs rounded-md border border-input bg-transparent px-2 py-1.5"
                  />
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setRejectingId(null);
                        setRejectionReason('');
                      }}
                    >
                      {t('common.cancel')}
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="destructive"
                      onClick={() => confirmReject(r.id)}
                      disabled={isSubmitting}
                    >
                      {t('moderation.action.reject')}
                    </Button>
                  </div>
                </div>
              )}
            </TableCell>
            <TableCell className="px-5 py-4 text-sm">
              {r.author.firstName} {r.author.lastName}
            </TableCell>
            <TableCell className="px-5 py-4">
              <StarRating value={r.rating} size="sm" />
            </TableCell>
            <TableCell className="px-5 py-4">{statusBadge(r, t)}</TableCell>
            <TableCell className="px-5 py-4 text-sm text-muted-foreground">
              {formatDate(r.createdAt)}
            </TableCell>
            <TableCell className="px-5 py-4 text-right">
              <div className="inline-flex items-center gap-1 flex-wrap justify-end">
                {r.status !== 'approved' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => act(r.id, 'approve')}
                    disabled={isSubmitting}
                    title={t('moderation.action.approve')}
                  >
                    <Check className="w-4 h-4 text-green-600" />
                  </Button>
                )}
                {r.status !== 'rejected' && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setRejectingId(r.id)}
                    disabled={isSubmitting}
                    title={t('moderation.action.reject')}
                  >
                    <X className="w-4 h-4 text-destructive" />
                  </Button>
                )}
                {r.isFlagged ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => act(r.id, 'unflag')}
                    disabled={isSubmitting}
                    title={t('moderation.action.unflag')}
                  >
                    <FlagOff className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => act(r.id, 'flag')}
                    disabled={isSubmitting}
                    title={t('moderation.action.flag')}
                  >
                    <Flag className="w-4 h-4 text-amber-500" />
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => act(r.id, 'delete')}
                  disabled={isSubmitting}
                  title={t('moderation.action.delete')}
                  className="text-destructive hover:text-destructive hover:bg-destructive/10"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
