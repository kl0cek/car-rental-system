'use client';

import { useSettings } from '@/contexts/SettingsContext';
import { translations, tFormat, type TranslationKey } from './translations';

export function useTranslation() {
  const { language } = useSettings();
  const dict = translations[language];
  const t = (key: TranslationKey, vars?: Record<string, string | number>): string => {
    const value = dict[key] ?? key;
    return vars ? tFormat(value, vars) : value;
  };
  return { t, language };
}
