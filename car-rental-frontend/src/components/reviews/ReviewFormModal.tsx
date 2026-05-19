'use client';

import { useEffect, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useTranslation } from '@/i18n/useTranslation';
import { useCreateReview, useUpdateReview } from '@/hooks/useReviewMutations';
import type { Review } from '@/types/review';
import { StarRating } from './StarRating';

interface ReviewFormModalProps {
  vehicleId: string;
  rentalId: string;
  vehicleLabel: string;
  /**
   * When provided we render the edit flow — pre-fill the form and call the
   * update endpoint on submit. When null/undefined, we render the create flow.
   */
  existingReview?: Review | null;
  onClose: () => void;
  onSuccess?: () => void;
}

const BODY_MAX = 2000;
const BODY_MIN = 10;

export function ReviewFormModal({
  vehicleId,
  rentalId,
  vehicleLabel,
  existingReview,
  onClose,
  onSuccess,
}: ReviewFormModalProps) {
  const { t } = useTranslation();
  const isEdit = !!existingReview;

  const [rating, setRating] = useState<number>(existingReview?.rating ?? 0);
  const [title, setTitle] = useState<string>(existingReview?.title ?? '');
  const [body, setBody] = useState<string>(existingReview?.body ?? '');
  const [validationError, setValidationError] = useState<string | null>(null);

  const create = useCreateReview();
  const update = useUpdateReview();
  const isSubmitting = create.isSubmitting || update.isSubmitting;
  const submitError = create.error ?? update.error;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) {
      setValidationError(t('reviews.form.errorRating'));
      return;
    }
    if (body.trim().length < BODY_MIN) {
      setValidationError(t('reviews.form.errorBody'));
      return;
    }
    setValidationError(null);

    const payload = {
      rating,
      title: title.trim() ? title.trim() : null,
      body: body.trim(),
    };

    try {
      if (isEdit && existingReview) {
        await update.submit(existingReview.id, payload);
      } else {
        await create.submit({
          vehicleId,
          rentalId,
          ...payload,
        });
      }
      onSuccess?.();
      onClose();
    } catch {
      // Errors surfaced via create.error / update.error below.
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-background rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 rounded-full p-1.5 bg-background/80 backdrop-blur-sm hover:bg-secondary transition-colors border border-border"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <header>
            <h2 className="text-xl font-bold text-foreground">
              {isEdit ? t('reviews.form.editTitle') : t('reviews.form.title')}
            </h2>
            <p className="text-sm text-muted-foreground mt-1">{vehicleLabel}</p>
            <p className="text-sm text-muted-foreground">{t('reviews.form.subtitle')}</p>
          </header>

          <div className="space-y-2">
            <Label>{t('reviews.form.rating')}</Label>
            <div className="flex items-center gap-3">
              <StarRating value={rating} size="lg" onChange={setRating} />
              <span className="text-sm text-muted-foreground">
                {rating > 0 ? `${rating} / 5` : t('reviews.form.ratingHint')}
              </span>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="review-title">{t('reviews.form.titleField')}</Label>
            <Input
              id="review-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder={t('reviews.form.titlePlaceholder')}
              maxLength={120}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="review-body">{t('reviews.form.body')}</Label>
            <textarea
              id="review-body"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder={t('reviews.form.bodyPlaceholder')}
              maxLength={BODY_MAX}
              rows={6}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
            <p className="text-xs text-muted-foreground">
              {t('reviews.form.bodyHint', { count: body.length })}
            </p>
          </div>

          {!isEdit && (
            <Alert>
              <AlertDescription>{t('reviews.form.pendingNotice')}</AlertDescription>
            </Alert>
          )}

          {validationError && <p className="text-sm text-destructive">{validationError}</p>}
          {submitError && <p className="text-sm text-destructive">{submitError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isSubmitting
                ? t('reviews.form.submitting')
                : isEdit
                  ? t('reviews.form.submitEditing')
                  : t('reviews.form.submit')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
