'use client';

import { ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface StepNavProps {
  onBack?: () => void;
  onNext?: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  nextLoading?: boolean;
  align?: 'between' | 'end';
}

export function StepNav({
  onBack,
  onNext,
  nextLabel = 'Next',
  nextDisabled,
  nextLoading,
  align = 'between',
}: StepNavProps) {
  const layout = align === 'end' ? 'flex justify-end pt-2' : 'flex justify-between';

  return (
    <div className={layout}>
      {onBack && (
        <Button variant="outline" onClick={onBack} className="gap-2" type="button">
          <ChevronLeft className="w-4 h-4" /> Back
        </Button>
      )}
      {onNext && (
        <Button
          onClick={onNext}
          disabled={nextDisabled || nextLoading}
          className="gap-2"
          type="button"
        >
          {nextLoading ? `${nextLabel}…` : nextLabel}
          {!nextLoading && <ChevronRight className="w-4 h-4" />}
        </Button>
      )}
    </div>
  );
}
