'use client';

import { useState } from 'react';
import { Save } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';
import { useCreateVehicle, type CreateVehicleInput } from '@/hooks/useCreateVehicle';
import { CATEGORIES, ENGINE_TYPES } from '@/data/vehicles/constants';
import type { CategoryName, EngineType } from '@/types/vehicle';

const CURRENT_YEAR = new Date().getFullYear();

const INITIAL: CreateVehicleInput = {
  brand: '',
  model: '',
  year: CURRENT_YEAR,
  licensePlate: '',
  color: '',
  category: 'economy',
  engineType: 'petrol',
  horsepower: 100,
  seats: 5,
  trunkCapacity: 400,
  mileage: 0,
  dailyBasePrice: 200,
  imageUrl: null,
};

interface SectionProps {
  titleKey: TranslationKey;
  children: React.ReactNode;
}

function Section({ titleKey, children }: SectionProps) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <CardTitle className="text-base">{t(titleKey)}</CardTitle>
      </CardHeader>
      <CardContent className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">{children}</CardContent>
    </Card>
  );
}

interface AddVehicleFormProps {
  onSuccess?: () => void;
}

export function AddVehicleForm({ onSuccess }: AddVehicleFormProps) {
  const { t } = useTranslation();
  const { createVehicle, isLoading, error } = useCreateVehicle();
  const [form, setForm] = useState<CreateVehicleInput>(INITIAL);
  const [success, setSuccess] = useState(false);

  function update<K extends keyof CreateVehicleInput>(key: K, value: CreateVehicleInput[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSuccess(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createVehicle(form);
      setSuccess(true);
      setForm(INITIAL);
      onSuccess?.();
    } catch {
      // error captured in hook
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Section titleKey="addVehicle.section.basic">
        <div className="space-y-1.5">
          <Label htmlFor="brand">{t('addVehicle.brand')}</Label>
          <Input id="brand" value={form.brand} onChange={(e) => update('brand', e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="model">{t('addVehicle.model')}</Label>
          <Input id="model" value={form.model} onChange={(e) => update('model', e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="year">{t('addVehicle.year')}</Label>
          <Input
            id="year"
            type="number"
            min={1900}
            max={CURRENT_YEAR + 1}
            value={form.year}
            onChange={(e) => update('year', Number(e.target.value))}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="plate">{t('addVehicle.licensePlate')}</Label>
          <Input
            id="plate"
            value={form.licensePlate}
            onChange={(e) => update('licensePlate', e.target.value.toUpperCase())}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="color">{t('addVehicle.color')}</Label>
          <Input id="color" value={form.color} onChange={(e) => update('color', e.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label>{t('addVehicle.category')}</Label>
          <Select
            value={form.category}
            onValueChange={(v: string) => update('category', v as CategoryName)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {CATEGORIES.map((c) => (
                <SelectItem key={c.value} value={c.value}>
                  {c.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </Section>

      <Section titleKey="addVehicle.section.specs">
        <div className="space-y-1.5">
          <Label>{t('addVehicle.engineType')}</Label>
          <Select
            value={form.engineType}
            onValueChange={(v: string) => update('engineType', v as EngineType)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ENGINE_TYPES.map((e) => (
                <SelectItem key={e.value} value={e.value}>
                  {e.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="hp">{t('addVehicle.horsepower')}</Label>
          <Input
            id="hp"
            type="number"
            min={1}
            value={form.horsepower}
            onChange={(e) => update('horsepower', Number(e.target.value))}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="seats">{t('addVehicle.seats')}</Label>
          <Input
            id="seats"
            type="number"
            min={1}
            max={9}
            value={form.seats}
            onChange={(e) => update('seats', Number(e.target.value))}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="trunk">{t('addVehicle.trunkCapacity')}</Label>
          <Input
            id="trunk"
            type="number"
            min={0}
            value={form.trunkCapacity}
            onChange={(e) => update('trunkCapacity', Number(e.target.value))}
            required
          />
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="mileage">{t('addVehicle.mileage')}</Label>
          <Input
            id="mileage"
            type="number"
            min={0}
            value={form.mileage}
            onChange={(e) => update('mileage', Number(e.target.value))}
            required
          />
        </div>
      </Section>

      <Section titleKey="addVehicle.section.pricing">
        <div className="space-y-1.5">
          <Label htmlFor="price">{t('addVehicle.dailyPrice')}</Label>
          <Input
            id="price"
            type="number"
            min={0}
            step="0.01"
            value={form.dailyBasePrice}
            onChange={(e) => update('dailyBasePrice', Number(e.target.value))}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="image">{t('addVehicle.imageUrl')}</Label>
          <Input
            id="image"
            type="url"
            value={form.imageUrl ?? ''}
            onChange={(e) => update('imageUrl', e.target.value || null)}
            placeholder="https://…"
          />
          <p className="text-xs text-muted-foreground">{t('addVehicle.imageUrlHint')}</p>
        </div>
      </Section>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {success && <p className="text-sm text-green-600">{t('addVehicle.success')}</p>}

      <div className="flex justify-end">
        <Button type="submit" disabled={isLoading} className="gap-2">
          <Save className="w-4 h-4" />
          {isLoading ? t('addVehicle.submitting') : t('addVehicle.submit')}
        </Button>
      </div>
    </form>
  );
}
