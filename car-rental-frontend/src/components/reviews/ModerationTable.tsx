'use client';

import { Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import { useDeleteReview } from '@/hooks/useReviewMutations';
import type { Review } from '@/types/review';
import { StarRating } from './StarRating';

interface ModerationTableProps {
  reviews: Review[];
  isLoading: boolean;
}

export function ModerationTable({ reviews, isLoading }: ModerationTableProps) {
  const { t } = useTranslation();
  const { submit: deleteReview, isSubmitting } = useDeleteReview();

  async function handleDelete(id: string) {
    if (!window.confirm(t('moderation.confirmDelete'))) return;
    try {
      await deleteReview(id);
    } catch {
      // error surfaced through the hook's submitError; logged to console too
    }
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
              <p className="text-sm text-foreground/90 whitespace-pre-line line-clamp-4">
                {r.comment ?? <span className="text-muted-foreground italic">—</span>}
              </p>
            </TableCell>
            <TableCell className="px-5 py-4 text-sm">
              {r.author.firstName} {r.author.lastName}
            </TableCell>
            <TableCell className="px-5 py-4">
              <StarRating value={r.rating} size="sm" />
            </TableCell>
            <TableCell className="px-5 py-4 text-sm text-muted-foreground">
              {formatDate(r.createdAt)}
            </TableCell>
            <TableCell className="px-5 py-4 text-right">
              <Button
                size="sm"
                variant="ghost"
                onClick={() => handleDelete(r.id)}
                disabled={isSubmitting}
                title={t('moderation.action.delete')}
                className="text-destructive hover:text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
