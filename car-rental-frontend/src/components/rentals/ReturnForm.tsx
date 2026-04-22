'use client';

import { useState } from 'react';
import Link from 'next/link';
import { RotateCcw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ErrorAlert } from '@/components/auth/ErrorAlert';
import { useReturnRental, type ReturnPayload } from '@/hooks/useReturnRental';
import type { RentalResponse } from '@/types/rental';

interface ReturnFormProps {
  rentalId: string;
  cancelHref: string;
  onSuccess: (rental: RentalResponse) => void;
}

export function ReturnForm({ rentalId, cancelHref, onSuccess }: ReturnFormProps) {
  const { returnRental, isLoading, error } = useReturnRental();

  const [mileageEnd, setMileageEnd] = useState('');
  const [fuelLevel, setFuelLevel] = useState('100');
  const [damageNotes, setDamageNotes] = useState('');
  const [damagePhotos, setDamagePhotos] = useState('');
  const [extraCharges, setExtraCharges] = useState('0');
  const [validationError, setValidationError] = useState<string | null>(null);

  async function handleSubmit(e: React.SyntheticEvent<HTMLFormElement>) {
    e.preventDefault();
    setValidationError(null);

    const mileage = Number(mileageEnd);
    const fuel = Number(fuelLevel);
    const extras = Number(extraCharges);

    if (!Number.isFinite(mileage) || mileage < 0) {
      setValidationError('Mileage must be a non-negative number.');
      return;
    }
    if (!Number.isFinite(fuel) || fuel < 0 || fuel > 100) {
      setValidationError('Fuel level must be between 0 and 100.');
      return;
    }
    if (!Number.isFinite(extras) || extras < 0) {
      setValidationError('Extra charges must be a non-negative number.');
      return;
    }

    const payload: ReturnPayload = {
      mileage_end: mileage,
      fuel_level_end: fuel,
      damage_notes: damageNotes.trim() || null,
      damage_photo_urls: damagePhotos
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean),
      extra_charges: extras,
    };

    try {
      const rental = await returnRental(rentalId, payload);
      onSuccess(rental);
    } catch (err) {
      console.error('Return failed', err);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <RotateCcw className="w-5 h-5" /> Vehicle return
        </CardTitle>
        <CardDescription>Fill in vehicle condition at time of return</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5" noValidate>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="mileage">Return mileage (km)</Label>
              <Input
                id="mileage"
                type="number"
                min="0"
                required
                value={mileageEnd}
                onChange={(e) => setMileageEnd(e.target.value)}
                placeholder="e.g. 46200"
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
            <Label htmlFor="damage">Damage notes (optional)</Label>
            <Input
              id="damage"
              value={damageNotes}
              onChange={(e) => setDamageNotes(e.target.value)}
              placeholder="Describe any damage…"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="damagePhotos">Damage photo URLs (comma-separated, optional)</Label>
            <Input
              id="damagePhotos"
              value={damagePhotos}
              onChange={(e) => setDamagePhotos(e.target.value)}
              placeholder="https://…, https://…"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="extra">Extra charges (PLN)</Label>
            <Input
              id="extra"
              type="number"
              min="0"
              step="0.01"
              value={extraCharges}
              onChange={(e) => setExtraCharges(e.target.value)}
              placeholder="0.00"
            />
          </div>

          <ErrorAlert message={validationError ?? error} />

          <div className="flex gap-3">
            <Button variant="outline" type="button" asChild>
              <Link href={cancelHref}>Cancel</Link>
            </Button>
            <Button type="submit" disabled={isLoading || !mileageEnd} className="flex-1 gap-2">
              <RotateCcw className="w-4 h-4" />
              {isLoading ? 'Processing…' : 'Confirm return'}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
