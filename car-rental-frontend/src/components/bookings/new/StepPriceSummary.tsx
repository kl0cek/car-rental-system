'use client';

import { Car } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { formatDate } from '@/lib/formatters';
import type { Vehicle } from '@/types/vehicle';
import { SectionHeader } from './SectionHeader';
import { StepNav } from './StepNav';
import Image from 'next/image';

const MS_PER_DAY = 86_400_000;

function diffInDays(from: string, to: string): number {
  return Math.max(1, Math.round((new Date(to).getTime() - new Date(from).getTime()) / MS_PER_DAY));
}

interface StepPriceSummaryProps {
  startDate: string;
  endDate: string;
  vehicle: Vehicle;
  onBack: () => void;
  onNext: () => void;
}

export function StepPriceSummary({
  startDate,
  endDate,
  vehicle,
  onBack,
  onNext,
}: StepPriceSummaryProps) {
  const days = diffInDays(startDate, endDate);
  const estimated = vehicle.dailyBasePrice * vehicle.category.priceMultiplier * days;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Price summary"
        description="Review your booking details before continuing."
      />

      <Card>
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-lg bg-secondary flex items-center justify-center shrink-0">
              {vehicle.imageUrl ? (
                <Image
                  src={vehicle.imageUrl}
                  className="w-full h-full object-cover rounded-lg"
                  alt=""
                />
              ) : (
                <Car className="w-7 h-7 text-muted-foreground" />
              )}
            </div>
            <div>
              <p className="font-semibold text-foreground">
                {vehicle.brand} {vehicle.model} ({vehicle.year})
              </p>
              <p className="text-sm text-muted-foreground capitalize">
                {vehicle.category.name} · {vehicle.seats} seats
              </p>
            </div>
          </div>

          <div className="border-t pt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Period</span>
              <span className="font-medium">
                {formatDate(startDate)} – {formatDate(endDate)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Duration</span>
              <span className="font-medium">
                {days} day{days !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Base price</span>
              <span>{vehicle.dailyBasePrice.toFixed(0)} PLN/day</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Category multiplier</span>
              <span>×{vehicle.category.priceMultiplier.toFixed(2)}</span>
            </div>
            <div className="flex justify-between border-t pt-2 font-semibold text-base">
              <span>Estimated total</span>
              <span>{estimated.toFixed(0)} PLN</span>
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            * Final price may differ based on your risk profile and fuel levels at return.
          </p>
        </CardContent>
      </Card>

      <StepNav onBack={onBack} onNext={onNext} />
    </div>
  );
}
