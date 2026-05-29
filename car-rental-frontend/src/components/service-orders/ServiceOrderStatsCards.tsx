'use client';

import { CalendarClock, Hammer, CheckCircle2, ListChecks } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useTranslation } from '@/i18n/useTranslation';
import { useServiceOrderStats } from '@/hooks/useServiceOrderStats';

export function ServiceOrderStatsCards() {
  const { t } = useTranslation();
  const { stats, isLoading } = useServiceOrderStats();

  const items = [
    {
      label: t('serviceOrders.stats.scheduled'),
      value: stats?.scheduled,
      icon: CalendarClock,
      tone: 'text-blue-600 bg-blue-500/10',
    },
    {
      label: t('serviceOrders.stats.inProgress'),
      value: stats?.inProgress,
      icon: Hammer,
      tone: 'text-amber-600 bg-amber-500/10',
    },
    {
      label: t('serviceOrders.stats.completed'),
      value: stats?.completed,
      icon: CheckCircle2,
      tone: 'text-emerald-600 bg-emerald-500/10',
    },
    {
      label: t('serviceOrders.stats.total'),
      value: stats?.total,
      icon: ListChecks,
      tone: 'text-foreground bg-secondary',
    },
  ] as const;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
      {items.map((it) => (
        <Card key={it.label}>
          <CardContent className="p-4 flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${it.tone}`}>
              <it.icon className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <p className="text-xs uppercase tracking-wide text-muted-foreground">{it.label}</p>
              {isLoading || it.value === undefined ? (
                <Skeleton className="h-6 w-12 mt-1" />
              ) : (
                <p className="text-xl font-semibold leading-tight">{it.value}</p>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
