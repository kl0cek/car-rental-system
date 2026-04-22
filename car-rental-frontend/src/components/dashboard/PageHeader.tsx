'use client';

import Link from 'next/link';
import { ChevronLeft } from 'lucide-react';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  backHref: string;
  title: string;
  subtitle?: ReactNode;
  action?: ReactNode;
}

export function PageHeader({ backHref, title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="flex items-center gap-3">
      <Link
        href={backHref}
        className="text-muted-foreground hover:text-foreground transition-colors"
        aria-label="Back"
      >
        <ChevronLeft className="w-5 h-5" />
      </Link>
      <div className="flex-1">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
