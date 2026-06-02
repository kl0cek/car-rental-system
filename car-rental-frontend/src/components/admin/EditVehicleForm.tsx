'use client';

import { useState } from 'react';
import { Save, Star, Trash2, ImagePlus, Loader2 } from 'lucide-react';
import Image from 'next/image';
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
import { useUpdateVehicle, type UpdateVehicleInput } from '@/hooks/vehicles/useUpdateVehicle';
import { useVehicleImages } from '@/hooks/vehicles/useVehicleImages';
import { useCategories } from '@/hooks/vehicles/useCategories';
import { ENGINE_TYPES, STATUS_CONFIG, VEHICLE_COLORS } from '@/data/vehicles/constants';
import type { EngineType, VehicleColor, VehicleDetail, VehicleStatus } from '@/types/vehicle';

const CURRENT_YEAR = new Date().getFullYear();
const ACCEPTED_MIME = ['image/jpeg', 'image/png', 'image/webp'];

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

interface EditVehicleFormProps {
  vehicle: VehicleDetail;
  onChanged?: () => void;
}

const STATUS_OPTIONS: VehicleStatus[] = ['available', 'rented', 'maintenance', 'out_of_service'];

export function EditVehicleForm({ vehicle, onChanged }: EditVehicleFormProps) {
  const { t } = useTranslation();
  const { categories, isLoading: categoriesLoading } = useCategories();
  const { updateVehicle, isLoading: updating, error: updateError } = useUpdateVehicle();
  const {
    uploadImage,
    deleteImage,
    setPrimary,
    isLoading: imagesBusy,
    error: imagesError,
  } = useVehicleImages();

  const [form, setForm] = useState({
    brand: vehicle.brand,
    model: vehicle.model,
    year: vehicle.year,
    licensePlate: vehicle.licensePlate,
    vin: vehicle.vin,
    color: vehicle.color,
    categoryId: vehicle.category.id,
    engineType: vehicle.engineType,
    horsepower: vehicle.horsepower,
    seats: vehicle.seats,
    trunkCapacity: vehicle.trunkCapacity,
    mileage: vehicle.mileage,
    dailyBasePrice: vehicle.dailyBasePrice,
    status: vehicle.status,
  });
  const [success, setSuccess] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  function update<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
    setSuccess(false);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const payload: UpdateVehicleInput = {
      brand: form.brand,
      model: form.model,
      year: form.year,
      licensePlate: form.licensePlate,
      vin: form.vin,
      color: form.color,
      categoryId: form.categoryId,
      engineType: form.engineType,
      horsepower: form.horsepower,
      seats: form.seats,
      trunkCapacity: form.trunkCapacity,
      mileage: form.mileage,
      dailyBasePrice: form.dailyBasePrice,
      status: form.status,
    };
    try {
      await updateVehicle(vehicle.id, payload);
      setSuccess(true);
      onChanged?.();
    } catch {
      // hook captures the message
    }
  }

  async function handleAddImages(files: FileList | null) {
    if (!files || files.length === 0) return;
    setUploadError(null);
    for (const file of Array.from(files)) {
      if (!ACCEPTED_MIME.includes(file.type)) {
        setUploadError(t('multiImage.invalidType'));
        continue;
      }
      try {
        // Upload sequentially: parallel calls would race the position counter
        // and produce inconsistent ordering on the gallery.
        await uploadImage(vehicle.id, file, vehicle.images.length === 0);
      } catch (err) {
        console.error('Image upload failed', err);
      }
    }
    onChanged?.();
  }

  async function handleSetPrimary(imageId: string) {
    try {
      await setPrimary(vehicle.id, imageId);
      onChanged?.();
    } catch (err) {
      console.error('Set primary failed', err);
    }
  }

  async function handleDeleteImage(imageId: string) {
    try {
      await deleteImage(vehicle.id, imageId);
      onChanged?.();
    } catch (err) {
      console.error('Delete image failed', err);
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
            value={form.categoryId}
            onValueChange={(v: string) => update('categoryId', v)}
            disabled={categoriesLoading}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
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
          <Label>{t('common.status')}</Label>
          <Select
            value={form.status}
            onValueChange={(v: string) => update('status', v as VehicleStatus)}
          >
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {STATUS_OPTIONS.map((s) => (
                <SelectItem key={s} value={s}>
                  <span className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${STATUS_CONFIG[s].dot}`} />
                    {STATUS_CONFIG[s].label}
                  </span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </Section>

      <Card>
        <CardHeader className="border-b pb-4 flex-row items-center justify-between space-y-0">
          <CardTitle className="text-base">{t('editVehicle.gallery')}</CardTitle>
          <label className="cursor-pointer">
            <input
              type="file"
              accept={ACCEPTED_MIME.join(',')}
              multiple
              className="hidden"
              onChange={(e) => {
                handleAddImages(e.target.files);
                e.target.value = '';
              }}
            />
            <Button type="button" variant="outline" size="sm" asChild={false} disabled={imagesBusy}>
              {imagesBusy ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <ImagePlus className="w-4 h-4 mr-2" />
              )}
              {t('multiImage.add')}
            </Button>
          </label>
        </CardHeader>
        <CardContent className="pt-4">
          {uploadError && <p className="text-sm text-destructive mb-3">{uploadError}</p>}
          {imagesError && <p className="text-sm text-destructive mb-3">{imagesError}</p>}
          {vehicle.images.length === 0 ? (
            <p className="text-sm text-muted-foreground py-6 text-center">
              {t('multiImage.empty')}
            </p>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {vehicle.images
                .slice()
                .sort((a, b) => {
                  if (a.isPrimary !== b.isPrimary) return a.isPrimary ? -1 : 1;
                  return a.position - b.position;
                })
                .map((img) => (
                  <div
                    key={img.id}
                    className="relative group rounded-lg overflow-hidden border border-border aspect-video bg-muted"
                  >
                    <Image src={img.url} alt="" fill className="object-cover" />
                    {img.isPrimary && (
                      <span className="absolute top-1.5 left-1.5 inline-flex items-center gap-1 bg-primary text-primary-foreground text-[10px] uppercase tracking-wider rounded px-1.5 py-0.5">
                        <Star className="w-2.5 h-2.5" />
                        {t('multiImage.primary')}
                      </span>
                    )}
                    <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      {!img.isPrimary && (
                        <Button
                          type="button"
                          size="icon"
                          variant="secondary"
                          onClick={() => handleSetPrimary(img.id)}
                          disabled={imagesBusy}
                          aria-label={t('multiImage.setPrimary')}
                        >
                          <Star className="w-3.5 h-3.5" />
                        </Button>
                      )}
                      <Button
                        type="button"
                        size="icon"
                        variant="destructive"
                        onClick={() => handleDeleteImage(img.id)}
                        disabled={imagesBusy}
                        aria-label={t('common.delete')}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </CardContent>
      </Card>

      {updateError && <p className="text-sm text-destructive">{updateError}</p>}
      {success && <p className="text-sm text-green-600">{t('editVehicle.saved')}</p>}

      <div className="flex justify-end">
        <Button type="submit" disabled={updating} className="gap-2">
          <Save className="w-4 h-4" />
          {updating ? t('common.loading') : t('common.save')}
        </Button>
      </div>
    </form>
  );
}
