'use client';

import { formatDate, getInitials } from '@/lib/formatters';
import type { Review } from '@/types/review';
import { StarRating } from './StarRating';

interface ReviewItemProps {
  review: Review;
}

export function ReviewItem({ review }: ReviewItemProps) {
  return (
    <article className="border-b border-border pb-5 last:border-b-0 last:pb-0">
      <header className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-secondary flex items-center justify-center font-medium text-sm text-foreground shrink-0">
          {getInitials(review.author.firstName, review.author.lastName || ' ')}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-medium text-foreground">
              {review.author.firstName} {review.author.lastName}
            </p>
            <span className="text-xs text-muted-foreground">{formatDate(review.createdAt)}</span>
          </div>
          <StarRating value={review.rating} size="sm" className="mt-1" />
        </div>
      </header>

      {review.comment && (
        <p className="mt-3 text-sm text-foreground/90 whitespace-pre-line">{review.comment}</p>
      )}
    </article>
  );
}
