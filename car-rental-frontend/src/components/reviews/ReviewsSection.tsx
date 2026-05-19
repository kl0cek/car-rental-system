'use client';

import { useState } from 'react';
import { MessageSquare } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useVehicleReviews } from '@/hooks/useVehicleReviews';
import { useTranslation } from '@/i18n/useTranslation';
import type { ReviewSort } from '@/types/review';
import type { TranslationKey } from '@/i18n/translations';
import { StarRating } from './StarRating';
import { ReviewItem } from './ReviewItem';

const SORT_OPTIONS: ReviewSort[] = ['newest', 'top_rating', 'low_rating', 'most_helpful'];

interface ReviewsSectionProps {
  vehicleId: string;
}

export function ReviewsSection({ vehicleId }: ReviewsSectionProps) {
  const { t } = useTranslation();
  const [sort, setSort] = useState<ReviewSort>('newest');
  const [page, setPage] = useState(1);

  const { data, isLoading, pageSize } = useVehicleReviews({ vehicleId, sort, page });

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <section className="space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div>
          <h3 className="text-lg font-semibold text-foreground">{t('reviews.section.title')}</h3>
          <p className="text-sm text-muted-foreground">{t('reviews.section.subtitle')}</p>
        </div>

        {data && data.total > 0 && (
          <div className="text-right">
            <div className="flex items-center gap-2 justify-end">
              <span className="text-2xl font-bold text-foreground">
                {data.averageRating?.toFixed(1) ?? '—'}
              </span>
              <StarRating value={data.averageRating ?? 0} size="md" />
            </div>
            <p className="text-xs text-muted-foreground">
              {data.total === 1
                ? t('reviews.basedOn.one')
                : t('reviews.basedOn', { count: data.total })}
            </p>
          </div>
        )}
      </div>

      <div className="flex justify-end">
        <Select
          value={sort}
          onValueChange={(v) => {
            setSort(v as ReviewSort);
            setPage(1);
          }}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder={t('reviews.sort.label')} />
          </SelectTrigger>
          <SelectContent>
            {SORT_OPTIONS.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {t(`reviews.sort.${opt}` as TranslationKey)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading && !data ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full rounded-lg" />
          ))}
        </div>
      ) : !data || data.items.length === 0 ? (
        <div className="py-10 text-center">
          <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mx-auto mb-3">
            <MessageSquare className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="font-medium text-foreground">{t('reviews.empty')}</p>
          <p className="text-sm text-muted-foreground mt-1">{t('reviews.emptyDesc')}</p>
        </div>
      ) : (
        <div className="space-y-5">
          {data.items.map((review) => (
            <ReviewItem key={review.id} review={review} />
          ))}
        </div>
      )}

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-2">
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
    </section>
  );
}
