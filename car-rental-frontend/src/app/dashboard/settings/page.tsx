'use client';

import { Moon, Sun, Globe } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useSettings, type Theme, type Language } from '@/contexts/SettingsContext';
import { SettingsCard } from '@/components/settings/SettingsCard';
import { AccountCard } from '@/components/settings/AccountCard';

function OptionButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border text-sm font-medium transition-colors ${
        active
          ? 'bg-primary text-primary-foreground border-primary'
          : 'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'
      }`}
    >
      {children}
    </button>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, language, setTheme, setLanguage } = useSettings();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Manage your account and preferences</p>
      </div>

      <AccountCard user={user} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SettingsCard icon={Sun} title="Appearance" description="Choose light or dark theme">
          <div className="flex gap-3">
            <OptionButton active={theme === 'light'} onClick={() => setTheme('light' as Theme)}>
              <Sun className="w-4 h-4" /> Light
            </OptionButton>
            <OptionButton active={theme === 'dark'} onClick={() => setTheme('dark' as Theme)}>
              <Moon className="w-4 h-4" /> Dark
            </OptionButton>
          </div>
        </SettingsCard>

        <SettingsCard
          icon={Globe}
          title="Language"
          description="Interface language (translations coming soon)"
        >
          <div className="flex gap-3">
            <OptionButton active={language === 'en'} onClick={() => setLanguage('en' as Language)}>
              🇬🇧 English
            </OptionButton>
            <OptionButton active={language === 'pl'} onClick={() => setLanguage('pl' as Language)}>
              🇵🇱 Polski
            </OptionButton>
          </div>
        </SettingsCard>
      </div>
    </div>
  );
}
