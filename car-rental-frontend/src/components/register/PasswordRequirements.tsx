'use client';

import { Check } from 'lucide-react';
import type { PasswordRequirement } from '@/types/register';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

interface PasswordRequirementsProps {
  requirements: PasswordRequirement[];
}

export function PasswordRequirements({ requirements }: PasswordRequirementsProps) {
  const { t } = useTranslation();
  return (
    <ul className="space-y-1.5 pt-2">
      {requirements.map((req) => {
        const label = t(req.label as TranslationKey);
        return (
          <li key={req.label} className="flex items-center gap-2 text-xs">
            <div
              className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${
                req.met ? 'bg-accent text-accent-foreground' : 'bg-muted'
              }`}
              aria-hidden="true"
            >
              {req.met && <Check className="w-3 h-3" />}
            </div>
            <span className={req.met ? 'text-foreground' : 'text-muted-foreground'}>{label}</span>
          </li>
        );
      })}
    </ul>
  );
}
