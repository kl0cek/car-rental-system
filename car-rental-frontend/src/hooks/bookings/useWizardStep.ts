'use client';

import { useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

interface UseWizardStepOptions {
  stepCount: number;
  paramName?: string;
  canEnterStep?: (step: number) => boolean;
}

export function useWizardStep({
  stepCount,
  paramName = 'step',
  canEnterStep,
}: UseWizardStepOptions) {
  const router = useRouter();
  const searchParams = useSearchParams();

  const raw = Number(searchParams.get(paramName) ?? 0);
  const requested = Number.isFinite(raw)
    ? Math.max(0, Math.min(stepCount - 1, Math.trunc(raw)))
    : 0;
  const step = canEnterStep && !canEnterStep(requested) ? 0 : requested;

  const goToStep = useCallback(
    (next: number) => {
      const params = new URLSearchParams(searchParams.toString());
      if (next === 0) params.delete(paramName);
      else params.set(paramName, String(next));
      const qs = params.toString();
      router.push(qs ? `?${qs}` : '?', { scroll: false });
    },
    [router, searchParams, paramName]
  );

  return { step, goToStep };
}
