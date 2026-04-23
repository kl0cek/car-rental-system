'use client';

import { useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { useVehicles, type VehicleSearchParams } from '@/hooks/useVehicles';
import { PRICE_MIN, PRICE_MAX, YEAR_MIN, YEAR_MAX } from '@/types/vehicle';
import type { Vehicle } from '@/types/vehicle';
import { SectionHeader } from './SectionHeader';
import { StepNav } from './StepNav';
import { VehicleCard } from './VehicleCard';

const SKELETON_COUNT = 6;

function todayIso() {
  return new Date().toISOString().split('T')[0];
}

interface StepDatesAndVehicleProps {
  startDate: string;
  endDate: string;
  selectedVehicle: Vehicle | null;
  onStartDate: (value: string) => void;
  onEndDate: (value: string) => void;
  onSelectVehicle: (vehicle: Vehicle) => void;
  onNext: () => void;
}

export function StepDatesAndVehicle({
  startDate,
  endDate,
  selectedVehicle,
  onStartDate,
  onEndDate,
  onSelectVehicle,
  onNext,
}: StepDatesAndVehicleProps) {
  const today = useMemo(() => todayIso(), []);
  const datesValid = Boolean(startDate && endDate && endDate > startDate);

  const searchParams = useMemo<VehicleSearchParams>(
    () => ({
      category: null,
      engineType: null,
      priceRange: [PRICE_MIN, PRICE_MAX],
      yearRange: [YEAR_MIN, YEAR_MAX],
      minSeats: null,
      sortBy: 'brand',
      sortOrder: 'asc',
      page: 1,
      availableFrom: startDate,
      availableTo: endDate,
    }),
    [startDate, endDate]
  );

  const { vehicles, isLoading } = useVehicles(searchParams, { enabled: datesValid });

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Select dates and vehicle"
        description="Choose your rental period first, then pick a car."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="start">Start date</Label>
          <Input
            id="start"
            type="date"
            min={today}
            value={startDate}
            onChange={(e) => onStartDate(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="end">End date</Label>
          <Input
            id="end"
            type="date"
            min={startDate || today}
            value={endDate}
            onChange={(e) => onEndDate(e.target.value)}
          />
        </div>
      </div>

      {datesValid && (
        <>
          <p className="text-sm text-muted-foreground">
            Available vehicles for selected dates ({vehicles.length} found)
          </p>
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
                <Skeleton key={i} className="h-64 rounded-xl" />
              ))}
            </div>
          ) : vehicles.length === 0 ? (
            <p className="text-sm text-muted-foreground py-8 text-center">
              No vehicles available for these dates.
            </p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {vehicles.map((v) => (
                <VehicleCard
                  key={v.id}
                  vehicle={v}
                  selected={selectedVehicle?.id === v.id}
                  onSelect={onSelectVehicle}
                />
              ))}
            </div>
          )}
        </>
      )}

      <StepNav onNext={onNext} nextDisabled={!datesValid || !selectedVehicle} align="end" />
    </div>
  );
}
