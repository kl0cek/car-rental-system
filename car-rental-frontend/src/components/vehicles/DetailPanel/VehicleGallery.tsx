'use client';

import { useState, useMemo } from 'react';
import { Car } from 'lucide-react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import type { Vehicle } from '@/types/vehicle';
import { STATUS_CONFIG } from '@/data/vehicles/constants';

interface VehicleGalleryProps {
  vehicle: Vehicle;
}

export function VehicleGallery({ vehicle }: VehicleGalleryProps) {
  // Order: primary first, then by position. Falls back to imageUrl when the
  // vehicle has no image rows (legacy data path or freshly created vehicle).
  const ordered = useMemo(() => {
    const byPos = [...vehicle.images].sort((a, b) => {
      if (a.isPrimary !== b.isPrimary) return a.isPrimary ? -1 : 1;
      return a.position - b.position;
    });
    if (byPos.length > 0) return byPos.map((i) => i.url);
    return vehicle.imageUrl ? [vehicle.imageUrl] : [];
  }, [vehicle.images, vehicle.imageUrl]);

  // Key the state on vehicle.id so switching between vehicles inside the same
  // panel resets to the first thumbnail without an effect-driven cascade.
  const [stateForId, setStateForId] = useState({ id: vehicle.id, idx: 0 });
  if (stateForId.id !== vehicle.id) {
    setStateForId({ id: vehicle.id, idx: 0 });
  }
  const activeImg = stateForId.id === vehicle.id ? stateForId.idx : 0;
  const setActiveImg = (idx: number) => setStateForId({ id: vehicle.id, idx });

  const status = STATUS_CONFIG[vehicle.status];
  const activeUrl = ordered[activeImg] ?? null;

  return (
    <>
      <div className="relative aspect-video bg-linear-to-br from-secondary to-muted overflow-hidden rounded-t-2xl">
        {activeUrl ? (
          <Image
            src={activeUrl}
            alt={`${vehicle.brand} ${vehicle.model}`}
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2">
            <Car className="w-20 h-20 text-muted-foreground/20" />
          </div>
        )}
        <Badge className={`absolute top-3 left-3 ${status.className}`}>{status.label}</Badge>
      </div>

      {ordered.length > 1 && (
        <div className="flex gap-2 px-6 pt-3 overflow-x-auto">
          {ordered.map((url, i) => (
            <button
              key={url}
              type="button"
              onClick={() => setActiveImg(i)}
              className={`relative w-16 h-12 rounded-lg overflow-hidden border-2 transition-colors shrink-0 bg-linear-to-br from-secondary to-muted flex items-center justify-center ${
                activeImg === i ? 'border-primary' : 'border-transparent hover:border-border'
              }`}
              aria-label={`Zdjęcie ${i + 1}`}
            >
              <Image src={url} alt={`Zdjęcie ${i + 1}`} fill className="object-cover" />
            </button>
          ))}
        </div>
      )}
    </>
  );
}
