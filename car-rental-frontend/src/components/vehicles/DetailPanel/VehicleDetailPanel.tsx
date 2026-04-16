'use client';

import { useState, useCallback, useEffect } from 'react';
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import type { Vehicle } from '@/types/vehicle';
import { STATUS_CONFIG, ENGINE_CONFIG, CATEGORY_LABELS } from '@/data/vehicles/constants';
import { VehicleGallery } from './VehicleGallery';
import { VehicleSpecs } from './VehicleSpec';
import { AvailabilityCalendar } from './AvailabilityCalendar';
import { PriceCalculator } from './PriceCalculator';

interface VehicleDetailPanelProps {
  vehicle: Vehicle;
  onClose: () => void;
}

export function VehicleDetailPanel({ vehicle, onClose }: VehicleDetailPanelProps) {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const status = STATUS_CONFIG[vehicle.status];
  const engine = ENGINE_CONFIG[vehicle.engineType];
  const EngineIcon = engine.Icon;
  const isAvailable = vehicle.status === 'available';

  const days =
    dateFrom && dateTo
      ? Math.max(
          0,
          Math.ceil((new Date(dateTo).getTime() - new Date(dateFrom).getTime()) / 86400000)
        )
      : 0;
  const finalTotal = days * vehicle.dailyBasePrice * vehicle.category.priceMultiplier;

  const handleDatesChange = useCallback((from: string, to: string) => {
    setDateFrom(from);
    setDateTo(to);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-background rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 rounded-full p-1.5 bg-background/80 backdrop-blur-sm hover:bg-secondary transition-colors border border-border"
          aria-label="Zamknij"
        >
          <X className="w-4 h-4" />
        </button>

        <VehicleGallery vehicle={vehicle} />

        <div className="p-6 space-y-6">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <Badge variant="secondary">{CATEGORY_LABELS[vehicle.category.name]}</Badge>
              <Badge variant="outline" className="gap-1">
                <EngineIcon className="w-3 h-3" />
                {engine.label}
              </Badge>
            </div>
            <h2 className="text-2xl font-bold text-foreground">
              {vehicle.brand} {vehicle.model}
            </h2>
            <p className="text-muted-foreground">
              {vehicle.year} · {vehicle.color}
            </p>
          </div>

          <Separator />

          <VehicleSpecs vehicle={vehicle} />

          <Separator />

          <AvailabilityCalendar
            vehicle={vehicle}
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDatesChange={handleDatesChange}
          />

          <Separator />

          <PriceCalculator
            vehicle={vehicle}
            dateFrom={dateFrom}
            dateTo={dateTo}
            onDateFromChange={setDateFrom}
            onDateToChange={setDateTo}
          />

          {/* TODO: podpiąć pod POST /api/reservations gdy endpoint będzie gotowy */}
          <Button className="w-full" size="lg" disabled={!isAvailable || days === 0}>
            {!isAvailable
              ? 'Pojazd niedostępny'
              : days === 0
                ? 'Wybierz daty, aby zarezerwować'
                : `Zarezerwuj za ${finalTotal.toFixed(0)} PLN`}
          </Button>
        </div>
      </div>
    </div>
  );
}
