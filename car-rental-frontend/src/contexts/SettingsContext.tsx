'use client';

import { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'light' | 'dark';
export type Language = 'en' | 'pl';

interface SettingsContextValue {
  theme: Theme;
  language: Language;
  setTheme: (t: Theme) => void;
  setLanguage: (l: Language) => void;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('light');
  const [language, setLanguageState] = useState<Language>('en');

  useEffect(() => {
    const VALID_THEMES: Theme[] = ['light', 'dark'];
    const VALID_LANGS: Language[] = ['en', 'pl'];

    const raw = localStorage.getItem('theme');
    const savedTheme: Theme = VALID_THEMES.includes(raw as Theme) ? (raw as Theme) : 'light';

    const rawLang = localStorage.getItem('language');
    const savedLang: Language = VALID_LANGS.includes(rawLang as Language) ? (rawLang as Language) : 'en';

    setThemeState(savedTheme);
    setLanguageState(savedLang);
    localStorage.setItem('theme', savedTheme);
    localStorage.setItem('language', savedLang);
    document.documentElement.classList.toggle('dark', savedTheme === 'dark');
  }, []);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    localStorage.setItem('theme', t);
    document.documentElement.classList.toggle('dark', t === 'dark');
  };

  const setLanguage = (l: Language) => {
    setLanguageState(l);
    localStorage.setItem('language', l);
  };

  return (
    <SettingsContext.Provider value={{ theme, language, setTheme, setLanguage }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
}
