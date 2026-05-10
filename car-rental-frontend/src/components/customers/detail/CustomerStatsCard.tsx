'use client';

import { CalendarCheck, Coins, Ban, AlertOctagon, Receipt } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { CustomerStats } from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';

interface CustomerStatsCardProps {
  stats: CustomerStats;
}

export function CustomerStatsCard({ stats }: CustomerStatsCardProps) {
  const { t } = useTranslation();

  const items = [
    { icon: Receipt, label: t('customerDetail.stats.total'), value: stats.totalRentals },
    {
      icon: CalendarCheck,
      label: t('customerDetail.stats.completed'),
      value: stats.completedRentals,
    },
    { icon: Ban, label: t('customerDetail.stats.cancelled'), value: stats.cancelledRentals },
    {
      icon: Coins,
      label: t('customerDetail.stats.spent'),
      value: `${stats.totalSpent.toFixed(0)} PLN`,
    },
    {
      icon: AlertOctagon,
      label: t('customerDetail.stats.incidents'),
      value: stats.incidentCount,
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{t('customerDetail.statsTitle')}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {items.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.label}
                className="rounded-lg border border-border p-3 flex flex-col gap-1.5"
              >
                <Icon className="w-4 h-4 text-muted-foreground" />
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-lg font-semibold">{item.value}</p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
