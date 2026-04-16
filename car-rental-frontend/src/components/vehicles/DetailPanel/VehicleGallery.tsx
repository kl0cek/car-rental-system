'use client';

import { useState } from 'react';
import { Car } from 'lucide-react';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import type { Vehicle } from '@/types/vehicle';
import { STATUS_CONFIG } from '@/data/vehicles/constants';

// TODO: zastąpić listą zdjęć z GET /api/vehicles/{id}/images gdy backend gotowy
const THUMBNAIL_COUNT = 3;

interface VehicleGalleryProps {
  vehicle: Vehicle;
}

export function VehicleGallery({ vehicle }: VehicleGalleryProps) {
  const [activeImg, setActiveImg] = useState(0);

  const status = STATUS_CONFIG[vehicle.status];
  const thumbnails = Array.from({ length: THUMBNAIL_COUNT }, (_, i) =>
    i === 0 ? vehicle.imageUrl : null
  );
  const activeIsReal = activeImg === 0 && vehicle.imageUrl;

  return (
    <>
      <div className="relative aspect-video bg-linear-to-br from-secondary to-muted overflow-hidden rounded-t-2xl">
        {activeIsReal ? (
          <Image
            src={vehicle.imageUrl!}
            alt={`${vehicle.brand} ${vehicle.model}`}
            fill
            className="object-cover"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2">
            <Car className="w-20 h-20 text-muted-foreground/20" />
            {activeImg > 0 && (
              <p className="text-xs text-muted-foreground/40">Zdjęcie {activeImg + 1}</p>
            )}
          </div>
        )}
        <Badge className={`absolute top-3 left-3 ${status.className}`}>{status.label}</Badge>
      </div>

      <div className="flex gap-2 px-6 pt-3">
        {thumbnails.map((img, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setActiveImg(i)}
            className={`relative w-16 h-12 rounded-lg overflow-hidden border-2 transition-colors shrink-0 bg-linear-to-br from-secondary to-muted flex items-center justify-center ${
              activeImg === i ? 'border-primary' : 'border-transparent hover:border-border'
            }`}
            aria-label={`Zdjęcie ${i + 1}`}
          >
            {img ? (
              <Image src={img} alt={`Zdjęcie ${i + 1}`} fill className="object-cover" />
            ) : (
              <Car className="w-5 h-5 text-muted-foreground/30" />
            )}
          </button>
        ))}
      </div>
    </>
  );
}
