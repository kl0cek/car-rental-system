'use client';

import { useTranslation } from '@/i18n/useTranslation';

export function TermsCheckbox() {
  const { t } = useTranslation();
  return (
    <div className="flex items-start gap-2">
      <input
        type="checkbox"
        id="terms"
        className="w-4 h-4 mt-0.5 rounded border-input text-primary focus:ring-ring"
        required
      />
      <label htmlFor="terms" className="text-sm text-muted-foreground">
        {t('auth.terms')}
      </label>
    </div>
  );
}
