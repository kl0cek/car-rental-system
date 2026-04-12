'use client';

import { Car, Users, Zap } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import type { Vehicle } from '@/types/vehicle';
import {STATUS_CONFIG, ENGINE_CONFIG, CATEGORY_LABELS} from '@/data/vehicles/constants'

export function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  const status = STATUS_CONFIG[vehicle.status];
  const engine = ENGINE_CONFIG[vehicle.engineType];
  const EngineIcon = engine.Icon;
  const isAvailable = vehicle.status === 'available';

  return (
    <Card className="overflow-hidden group hover:shadow-md transition-all duration-200">
      <div className="relative aspect-video bg-linear-to-br from-secondary to-muted overflow-hidden">
        {vehicle.imageUrl ? (
          <img
            src={vehicle.imageUrl}
            alt={`${vehicle.brand} ${vehicle.model}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Car className="w-14 h-14 text-muted-foreground/20" />
          </div>
        )}
        <Badge className={`absolute top-2 right-2 ${status.className}`}>
          {status.label}
        </Badge>
      </div>

      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <Badge variant="secondary" className="text-xs">
            {CATEGORY_LABELS[vehicle.category.name]}
          </Badge>
          <Badge variant="outline" className="text-xs gap-1">
            <EngineIcon className="w-3 h-3" />
            {engine.label}
          </Badge>
        </div>

        <div>
          <h3 className="font-semibold text-foreground leading-tight">
            {vehicle.brand} {vehicle.model}
          </h3>
          <p className="text-sm text-muted-foreground">
            {vehicle.year} · {vehicle.color}
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            {vehicle.seats} seats
          </span>
          <span className="flex items-center gap-1">
            <Zap className="w-3.5 h-3.5" />
            {vehicle.horsepower} hp
          </span>
          <span>{vehicle.mileage.toLocaleString()} km</span>
        </div>

        <div className="flex items-center justify-between pt-1 border-t border-border">
          <div>
            <span className="text-lg font-bold text-foreground">
              {vehicle.dailyBasePrice.toFixed(0)} PLN
            </span>
            <span className="text-xs text-muted-foreground"> /day</span>
          </div>
          <Button size="sm" disabled={!isAvailable}>
            {isAvailable ? 'Reserve' : 'Unavailable'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
