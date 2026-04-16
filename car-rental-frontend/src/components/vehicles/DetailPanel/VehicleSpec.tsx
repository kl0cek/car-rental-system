'use client';

import type { Vehicle } from '@/types/vehicle';
import { ENGINE_CONFIG, CATEGORY_LABELS } from '@/data/vehicles/constants';

interface VehicleSpecsProps {
  vehicle: Vehicle;
}

export function VehicleSpecs({ vehicle }: VehicleSpecsProps) {
  const engine = ENGINE_CONFIG[vehicle.engineType];

  const specs = [
    { label: 'Marka', value: vehicle.brand },
    { label: 'Model', value: vehicle.model },
    { label: 'Rok', value: vehicle.year },
    { label: 'Kolor', value: vehicle.color },
    { label: 'Silnik', value: engine.label },
    { label: 'Moc', value: `${vehicle.horsepower} KM` },
    { label: 'Liczba miejsc', value: vehicle.seats },
    { label: 'Bagażnik', value: `${vehicle.trunkCapacity} L` },
    { label: 'Przebieg', value: `${vehicle.mileage.toLocaleString()} km` },
    { label: 'Tablica rej.', value: vehicle.licensePlate },
    { label: 'Kategoria', value: CATEGORY_LABELS[vehicle.category.name] },
    { label: 'Mnożnik kategorii', value: `×${vehicle.category.priceMultiplier.toFixed(2)}` },
  ];

  return (
    <div>
      <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground mb-3">
        Pełna specyfikacja
      </h3>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {specs.map(({ label, value }) => (
          <div key={label} className="bg-secondary/50 rounded-lg p-3">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</p>
            <p className="text-sm font-medium text-foreground mt-0.5">{value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
