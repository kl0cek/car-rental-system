'use client';

import { useMemo, useState } from 'react';
import { Save } from 'lucide-react';
import { useRouter } from 'next/navigation';
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
import { useCategories } from '@/hooks/useCategories';
import { ENGINE_TYPES, VEHICLE_COLORS } from '@/data/vehicles/constants';
import type { CategoryName, EngineType, VehicleColor } from '@/types/vehicle';
import { MultiImageUpload, type PendingImage } from './MultiImageUpload';

const CURRENT_YEAR = new Date().getFullYear();

interface FormState {
  brand: string;
  model: string;
  year: number;
  licensePlate: string;
  vin: string;
  color: VehicleColor;
  categoryId: string;
  engineType: EngineType;
  horsepower: number;
  seats: number;
  trunkCapacity: number;
  mileage: number;
  dailyBasePrice: number;
}

const INITIAL: FormState = {
  brand: '',
  model: '',
  year: CURRENT_YEAR,
  licensePlate: '',
  vin: '',
  color: 'white',
  categoryId: '',
  engineType: 'petrol',
  horsepower: 100,
  seats: 5,
  trunkCapacity: 400,
  mileage: 0,
  dailyBasePrice: 200,
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
  const router = useRouter();
  const { createVehicle, isLoading, error } = useCreateVehicle();
  const { categories, isLoading: categoriesLoading } = useCategories();
  const [form, setForm] = useState<FormState>(INITIAL);
  const [pending, setPending] = useState<PendingImage[]>([]);
  const [primaryIndex, setPrimaryIndex] = useState(-1);
  const [success, setSuccess] = useState(false);

  // Auto-pick the first category once it loads — saves the user a click and
  // keeps the form valid by construction (categoryId is required).
  const effectiveCategoryId = useMemo(() => {
    if (form.categoryId) return form.categoryId;
    return categories[0]?.id ?? '';
  }, [form.categoryId, categories]);

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSuccess(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!effectiveCategoryId) return;

    // Reorder uploads so the chosen primary file is sent first — backend
    // marks the first uploaded image as primary by convention.
    const orderedFiles = pending.map((p) => p.file);
    if (primaryIndex > 0 && primaryIndex < orderedFiles.length) {
      const [primary] = orderedFiles.splice(primaryIndex, 1);
      orderedFiles.unshift(primary);
    }

    const payload: CreateVehicleInput = {
      brand: form.brand,
      model: form.model,
      year: form.year,
      licensePlate: form.licensePlate,
      vin: form.vin,
      color: form.color,
      categoryId: effectiveCategoryId,
      // Resolve the human-readable category name for backwards compatibility
      // with the older hook signature; not used by the request itself.
      category:
        (categories.find((c) => c.id === effectiveCategoryId)?.name as CategoryName) ?? 'economy',
      engineType: form.engineType,
      horsepower: form.horsepower,
      seats: form.seats,
      trunkCapacity: form.trunkCapacity,
      mileage: form.mileage,
      dailyBasePrice: form.dailyBasePrice,
      images: orderedFiles,
    };

    try {
      const created = await createVehicle(payload);
      setSuccess(true);
      setForm(INITIAL);
      setPending([]);
      setPrimaryIndex(-1);
      onSuccess?.();
      // After a successful create take the operator to the edit page so they
      // can fine-tune the gallery / spec without re-loading from the list.
      router.push(`/dashboard/admin/vehicles/${created.id}/edit`);
    } catch {
      // hook captures the message; nothing else to do here
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Section titleKey="addVehicle.section.basic">
        <div className="space-y-1.5">
          <Label htmlFor="brand">{t('addVehicle.brand')}</Label>
          <Input
            id="brand"
            value={form.brand}
            onChange={(e) => update('brand', e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="model">{t('addVehicle.model')}</Label>
          <Input
            id="model"
            value={form.model}
            onChange={(e) => update('model', e.target.value)}
            required
          />
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
          <Label htmlFor="vin">{t('addVehicle.vin')}</Label>
          <Input
            id="vin"
            value={form.vin}
            onChange={(e) => update('vin', e.target.value.toUpperCase())}
            maxLength={17}
            minLength={17}
            placeholder="17 characters"
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label>{t('addVehicle.color')}</Label>
          <Select
            value={form.color}
            onValueChange={(v: string) => update('color', v as VehicleColor)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {VEHICLE_COLORS.map((c) => (
                <SelectItem key={c} value={c}>
                  {t(`color.${c}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label>{t('addVehicle.category')}</Label>
          <Select
            value={effectiveCategoryId || undefined}
            onValueChange={(v: string) => update('categoryId', v)}
            disabled={categoriesLoading || categories.length === 0}
          >
            <SelectTrigger className="w-full">
              <SelectValue
                placeholder={categoriesLoading ? t('common.loading') : t('filters.any')}
              />
            </SelectTrigger>
            <SelectContent>
              {categories.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
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
            <SelectTrigger className="w-full">
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
        <div className="space-y-1.5 sm:col-span-2">
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
      </Section>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle className="text-base">{t('addVehicle.section.images')}</CardTitle>
        </CardHeader>
        <CardContent className="pt-4">
          <MultiImageUpload
            pending={pending}
            onChange={setPending}
            primaryIndex={primaryIndex}
            onPrimaryChange={setPrimaryIndex}
          />
        </CardContent>
      </Card>

      {error && <p className="text-sm text-destructive">{error}</p>}
      {success && <p className="text-sm text-green-600">{t('addVehicle.success')}</p>}

      <div className="flex justify-end">
        <Button type="submit" disabled={isLoading || !effectiveCategoryId} className="gap-2">
          <Save className="w-4 h-4" />
          {isLoading ? t('addVehicle.submitting') : t('addVehicle.submit')}
        </Button>
      </div>
    </form>
  );
}
