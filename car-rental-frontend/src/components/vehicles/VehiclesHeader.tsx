'use client';

import { SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useTranslation } from '@/i18n/useTranslation';

interface VehiclesHeaderProps {
  total: number;
  isLoading: boolean;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export function VehiclesHeader({
  total,
  isLoading,
  sidebarOpen,
  onToggleSidebar,
}: VehiclesHeaderProps) {
  const { t } = useTranslation();
  return (
    <div className="flex items-center justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t('vehicles.title')}</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          {isLoading
            ? t('common.loading')
            : t(total === 1 ? 'vehicles.totalCount' : 'vehicles.totalCountPlural', {
                count: total,
              })}
        </p>
      </div>
      <Button variant="outline" size="sm" className="lg:hidden" onClick={onToggleSidebar}>
        {sidebarOpen ? (
          <X className="w-4 h-4 mr-1.5" />
        ) : (
          <SlidersHorizontal className="w-4 h-4 mr-1.5" />
        )}
        {t('filters.title')}
      </Button>
    </div>
  );
}
