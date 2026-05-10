'use client';

import { Search, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { CATEGORIES, ENGINE_TYPES } from '@/data/vehicles/constants';
import type { CategoryName, EngineType } from '@/types/vehicle';
import { useTranslation } from '@/i18n/useTranslation';

interface FleetToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  engineType: EngineType | null;
  onEngineTypeChange: (value: EngineType | null) => void;
  category: CategoryName | null;
  onCategoryChange: (value: CategoryName | null) => void;
  onExport: () => void;
  exporting: boolean;
}

const ANY = '__any__';

export function FleetToolbar({
  search,
  onSearchChange,
  engineType,
  onEngineTypeChange,
  category,
  onCategoryChange,
  onExport,
  exporting,
}: FleetToolbarProps) {
  const { t } = useTranslation();

  const hasFilters = Boolean(search || engineType || category);
  const clearAll = () => {
    onSearchChange('');
    onEngineTypeChange(null);
    onCategoryChange(null);
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative flex-1 min-w-[200px]">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder={t('fleet.searchPlaceholder')}
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9 pr-9"
        />
        {search && (
          <button
            type="button"
            onClick={() => onSearchChange('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-secondary"
            aria-label="Clear search"
          >
            <X className="w-3.5 h-3.5 text-muted-foreground" />
          </button>
        )}
      </div>

      <Select
        value={engineType ?? ANY}
        onValueChange={(v) => onEngineTypeChange(v === ANY ? null : (v as EngineType))}
      >
        <SelectTrigger className="min-w-[140px]">
          <SelectValue placeholder={t('filters.engineType')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY}>{t('filters.any')}</SelectItem>
          {ENGINE_TYPES.map((e) => (
            <SelectItem key={e.value} value={e.value}>
              {e.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={category ?? ANY}
        onValueChange={(v) => onCategoryChange(v === ANY ? null : (v as CategoryName))}
      >
        <SelectTrigger className="min-w-[140px]">
          <SelectValue placeholder={t('filters.category')} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ANY}>{t('filters.any')}</SelectItem>
          {CATEGORIES.map((c) => (
            <SelectItem key={c.value} value={c.value}>
              {c.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {hasFilters && (
        <Button variant="ghost" size="sm" onClick={clearAll}>
          {t('filters.clear')}
        </Button>
      )}

      <div className="ml-auto">
        <Button variant="outline" size="sm" onClick={onExport} disabled={exporting}>
          {exporting ? t('common.loading') : t('fleet.exportCsv')}
        </Button>
      </div>
    </div>
  );
}
