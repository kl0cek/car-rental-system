'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Truck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { usePickupRental, type PickupPayload } from '@/hooks/usePickupRental';
import type { RentalResponse } from '@/types/rental';

interface PickupFormProps {
  reservationId: string;
  cancelHref: string;
  onSuccess: (rental: RentalResponse) => void;
}

export function PickupForm({ reservationId, cancelHref, onSuccess }: PickupFormProps) {
  const { pickup, isLoading, error } = usePickupRental();

  const [mileageStart, setMileageStart] = useState('');
  const [fuelLevel, setFuelLevel] = useState('100');
  const [photoUrls, setPhotoUrls] = useState('');
  const [signatureUrl, setSignatureUrl] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setValidationError(null);

    const mileage = Number(mileageStart);
    const fuel = Number(fuelLevel);

    if (!Number.isFinite(mileage) || mileage < 0) {
      setValidationError('Mileage must be a non-negative number.');
      return;
    }
    if (!Number.isFinite(fuel) || fuel < 0 || fuel > 100) {
      setValidationError('Fuel level must be between 0 and 100.');
      return;
    }

    const payload: PickupPayload = {
      mileage_start: mileage,
      fuel_level_start: fuel,
      photo_urls: photoUrls
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      client_signature_url: signatureUrl.trim() || null,
    };

    try {
      const rental = await pickup(reservationId, payload);
      onSuccess(rental);
    } catch (err) {
      console.error('Pickup failed', err);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Truck className="w-5 h-5" /> Vehicle handover
        </CardTitle>
        <CardDescription>Fill in vehicle condition at time of pickup</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="mileage">Current mileage (km)</Label>
              <Input
                id="mileage"
                type="number"
                min="0"
                required
                value={mileageStart}
                onChange={(e) => setMileageStart(e.target.value)}
                placeholder="e.g. 45000"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="fuel">Fuel level (%)</Label>
              <Input
                id="fuel"
                type="number"
                min="0"
                max="100"
                required
                value={fuelLevel}
                onChange={(e) => setFuelLevel(e.target.value)}
                placeholder="0–100"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="photos">Photo URLs (comma-separated, optional)</Label>
            <Input
              id="photos"
              value={photoUrls}
              onChange={(e) => setPhotoUrls(e.target.value)}
              placeholder="https://…, https://…"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="signature">Client signature URL (optional)</Label>
            <Input
              id="signature"
              value={signatureUrl}
              onChange={(e) => setSignatureUrl(e.target.value)}
              placeholder="https://…"
            />
          </div>

          <ErrorAlert message={validationError ?? error} />

          <div className="flex gap-3">
            <Button variant="outline" type="button" asChild>
              <Link href={cancelHref}>Cancel</Link>
            </Button>
            <Button type="submit" disabled={isLoading || !mileageStart} className="flex-1 gap-2">
              <Truck className="w-4 h-4" />
              {isLoading ? 'Processing…' : 'Confirm pickup'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
