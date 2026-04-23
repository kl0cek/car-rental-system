'use client';

import Image from 'next/image';
import { memo } from 'react';
import { Car, Fuel, Users } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import type { Vehicle } from '@/types/vehicle';

interface VehicleCardProps {
  vehicle: Vehicle;
  selected: boolean;
  onSelect: (vehicle: Vehicle) => void;
}

function VehicleCardImpl({ vehicle, selected, onSelect }: VehicleCardProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={() => onSelect(vehicle)}
      className={`w-full text-left rounded-xl border-2 overflow-hidden transition-all ${
        selected ? 'border-primary shadow-md' : 'border-border hover:border-primary/50'
      }`}
    >
      <div className="aspect-video bg-secondary relative">
        {vehicle.imageUrl ? (
          <Image
            src={vehicle.imageUrl}
            alt={`${vehicle.brand} ${vehicle.model}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Car className="w-10 h-10 text-muted-foreground/40" />
          </div>
        )}
        <Badge className="absolute top-2 left-2 capitalize">{vehicle.category.name}</Badge>
      </div>
      <div className="p-4">
        <p className="font-semibold text-foreground">
          {vehicle.brand} {vehicle.model} ({vehicle.year})
        </p>
        <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {vehicle.seats}
          </span>
          <span className="flex items-center gap-1">
            <Fuel className="w-3.5 h-3.5" />
            {vehicle.engineType}
          </span>
          <span>{vehicle.horsepower} hp</span>
        </div>
        <p className="mt-3 font-semibold text-foreground">
          {vehicle.dailyBasePrice.toFixed(0)} PLN
          <span className="text-xs font-normal text-muted-foreground"> / day</span>
        </p>
      </div>
    </button>
  );
}

export const VehicleCard = memo(VehicleCardImpl);
