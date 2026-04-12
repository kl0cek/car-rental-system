'use client';

import { useMemo } from 'react';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { CATEGORIES, ENGINE_TYPES } from '@/data/vehicles/constants';
import type { CategoryName, EngineType, SortableField } from '@/types/vehicle';
import { FilterToggleGroup } from '@/components/vehicles/FilterToggleGroup';
import { SortSelect } from '@/components/vehicles/SortSelect';
import { PriceRangeFilter } from '@/components/vehicles/PriceFilter';
import { YearRangeFilter } from '@/components/vehicles/YearFilter';
import { AvailabilityFilter } from '@/components/vehicles/AvaibilityFilter';
import { MinSeatsFilter } from '@/components/vehicles/SeatFilter';
import { isDefaultFilters, getDefaultFilters } from '@/lib/utils';

export interface FiltersState {
  category: CategoryName | null;
  engineType: EngineType | null;
  priceRange: [number, number];
  yearRange: [number, number];
  minSeats: number | null;
  availableFrom: string;
  availableTo: string;
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
}

interface VehicleFiltersProps {
  filters: FiltersState;
  onChange: (updates: Partial<FiltersState>) => void;
}

export function VehicleFilters({ filters, onChange }: VehicleFiltersProps) {
  const isDefault = useMemo(() => isDefaultFilters(filters), [filters]);

  return (
    <div className="space-y-5">
      <SortSelect
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
        onChange={(sortBy, sortOrder) => onChange({ sortBy, sortOrder })}
      />

      <Separator />

      <FilterToggleGroup
        label="Category"
        options={CATEGORIES}
        value={filters.category}
        onChange={(v) => onChange({ category: v })}
      />

      <Separator />

      <FilterToggleGroup
        label="Engine"
        options={ENGINE_TYPES}
        value={filters.engineType}
        onChange={(v) => onChange({ engineType: v })}
      />

      <Separator />

      <PriceRangeFilter
        value={filters.priceRange}
        onChange={(priceRange) => onChange({ priceRange })}
      />

      <Separator />

      <YearRangeFilter
        value={filters.yearRange}
        onChange={(yearRange) => onChange({ yearRange })}
      />

      <Separator />

      <MinSeatsFilter value={filters.minSeats} onChange={(minSeats) => onChange({ minSeats })} />

      <Separator />

      <AvailabilityFilter
        availableFrom={filters.availableFrom}
        availableTo={filters.availableTo}
        onChange={onChange}
      />

      {!isDefault && (
        <>
          <Separator />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onChange(getDefaultFilters())}
            className="w-full text-muted-foreground"
          >
            <X className="w-3.5 h-3.5 mr-1.5" />
            Clear filters
          </Button>
        </>
      )}
    </div>
  );
}
