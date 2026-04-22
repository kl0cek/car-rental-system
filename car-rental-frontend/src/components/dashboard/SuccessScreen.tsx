'use client';

import { Check, type LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

interface SuccessScreenProps {
  icon?: LucideIcon;
  title: string;
  description?: ReactNode;
  children?: ReactNode;
  actions: ReactNode;
}

export function SuccessScreen({
  icon: Icon = Check,
  title,
  description,
  children,
  actions,
}: SuccessScreenProps) {
  return (
    <div className="text-center space-y-4">
      <div className="w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
        <Icon className="w-7 h-7 text-green-600" />
      </div>
      <div>
        <p className="font-semibold">{title}</p>
        {description && <div className="text-sm text-muted-foreground mt-1">{description}</div>}
      </div>
      {children}
      <div className="flex flex-col gap-2">{actions}</div>
    </div>
  );
}
