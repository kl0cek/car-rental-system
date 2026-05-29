'use client';

import { Star } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StarRatingProps {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  /**
   * When provided, the component becomes interactive: clicking a star calls
   * `onChange(rating)`. Hovering shows a preview of the would-be rating.
   */
  onChange?: (value: number) => void;
  className?: string;
}

const SIZE_CLASS: Record<NonNullable<StarRatingProps['size']>, string> = {
  sm: 'w-3.5 h-3.5',
  md: 'w-4 h-4',
  lg: 'w-7 h-7',
};

export function StarRating({ value, max = 5, size = 'md', onChange, className }: StarRatingProps) {
  const interactive = !!onChange;
  return (
    <div
      className={cn('inline-flex items-center gap-0.5', className)}
      role={interactive ? 'radiogroup' : 'img'}
      aria-label={interactive ? undefined : `${value} / ${max}`}
    >
      {Array.from({ length: max }).map((_, i) => {
        const filled = i < Math.round(value);
        const StarEl = (
          <Star
            className={cn(
              SIZE_CLASS[size],
              filled ? 'fill-yellow-400 text-yellow-400' : 'text-muted-foreground/40'
            )}
          />
        );
        if (!interactive) return <span key={i}>{StarEl}</span>;
        return (
          <button
            key={i}
            type="button"
            onClick={() => onChange?.(i + 1)}
            className="cursor-pointer transition-transform hover:scale-110 active:scale-95"
            role="radio"
            aria-checked={value === i + 1}
            aria-label={`${i + 1}`}
          >
            {StarEl}
          </button>
        );
      })}
    </div>
  );
}
