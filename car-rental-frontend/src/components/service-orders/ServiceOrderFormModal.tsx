'use client';

import { useEffect, useMemo, useState } from 'react';
import { X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useTranslation } from '@/i18n/useTranslation';
import { useFleetVehicles } from '@/hooks/fleet/useFleetVehicles';
import {
  useCreateServiceOrder,
  useUpdateServiceOrder,
} from '@/hooks/service-orders/useServiceOrderMutations';
import { SERVICE_TYPES, type ServiceOrder, type ServiceType } from '@/types/serviceOrder';
import type { TranslationKey } from '@/i18n/translations';

interface Props {
  order?: ServiceOrder;
  defaultVehicleId?: string;
  onClose: () => void;
  onSuccess?: () => void;
}

const TYPE_KEYS: Record<ServiceType, TranslationKey> = {
  inspection: 'serviceOrders.type.inspection',
  repair: 'serviceOrders.type.repair',
  tire_swap: 'serviceOrders.type.tireSwap',
  wash: 'serviceOrders.type.wash',
};

function toLocalInput(dateString: string | undefined): string {
  if (!dateString) return '';
  const d = new Date(dateString);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function ServiceOrderFormModal({ order, defaultVehicleId, onClose, onSuccess }: Props) {
  const { t } = useTranslation();
  const isEdit = Boolean(order);

  // Fleet picker only needed when creating — edits keep the original vehicle
  // since switching cars mid-order would change vehicle-status side effects.
  const { vehicles, isLoading: vehiclesLoading } = useFleetVehicles({
    status: null,
    page: 1,
    sortBy: 'brand',
    sortOrder: 'asc',
  });

  const [vehicleId, setVehicleId] = useState<string>(
    order?.vehicleId ?? defaultVehicleId ?? '',
  );
  const [type, setType] = useState<ServiceType>(order?.type ?? 'inspection');
  const [description, setDescription] = useState<string>(order?.description ?? '');
  const [cost, setCost] = useState<string>(order?.cost?.toString() ?? '');
  const [scheduledLocal, setScheduledLocal] = useState<string>(
    toLocalInput(order?.scheduledDate ?? new Date().toISOString()),
  );
  const [validationError, setValidationError] = useState<string | null>(null);

  const { submit: createOrder, isSubmitting: creating, error: createError } =
    useCreateServiceOrder();
  const { submit: updateOrder, isSubmitting: updating, error: updateError } =
    useUpdateServiceOrder();

  const isSubmitting = creating || updating;
  const submitError = createError ?? updateError;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handler);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handler);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  const vehicleOptions = useMemo(() => vehicles, [vehicles]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicleId) {
      setValidationError(t('serviceOrders.form.errorVehicle'));
      return;
    }
    if (description.trim().length < 1) {
      setValidationError(t('serviceOrders.form.errorDescription'));
      return;
    }
    if (!scheduledLocal) {
      setValidationError(t('serviceOrders.form.errorScheduled'));
      return;
    }
    const parsedCost = cost.trim() === '' ? null : Number(cost);
    if (parsedCost !== null && (Number.isNaN(parsedCost) || parsedCost < 0)) {
      setValidationError(t('serviceOrders.form.errorCost'));
      return;
    }
    setValidationError(null);

    const scheduledIso = new Date(scheduledLocal).toISOString();

    try {
      if (isEdit && order) {
        await updateOrder(order.id, {
          type,
          description: description.trim(),
          cost: parsedCost,
          scheduledDate: scheduledIso,
        });
      } else {
        await createOrder({
          vehicleId,
          type,
          description: description.trim(),
          cost: parsedCost,
          scheduledDate: scheduledIso,
        });
      }
      onSuccess?.();
      onClose();
    } catch {
      // submitError is already populated
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-background rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 rounded-full p-1.5 bg-background/80 backdrop-blur-sm hover:bg-secondary transition-colors border border-border"
          aria-label="Close"
        >
          <X className="w-4 h-4" />
        </button>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <header>
            <h2 className="text-xl font-bold text-foreground">
              {isEdit ? t('serviceOrders.form.editTitle') : t('serviceOrders.form.createTitle')}
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              {t('serviceOrders.form.subtitle')}
            </p>
          </header>

          <div className="space-y-2">
            <Label htmlFor="so-vehicle">{t('serviceOrders.form.vehicle')}</Label>
            <Select
              value={vehicleId}
              onValueChange={setVehicleId}
              disabled={isEdit || vehiclesLoading}
            >
              <SelectTrigger id="so-vehicle" className="w-full">
                <SelectValue
                  placeholder={
                    vehiclesLoading
                      ? t('common.loading')
                      : t('serviceOrders.form.vehiclePlaceholder')
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {vehicleOptions.map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.brand} {v.model} · {v.licensePlate}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="so-type">{t('serviceOrders.form.type')}</Label>
            <Select value={type} onValueChange={(v) => setType(v as ServiceType)}>
              <SelectTrigger id="so-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SERVICE_TYPES.map((st) => (
                  <SelectItem key={st} value={st}>
                    {t(TYPE_KEYS[st])}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="so-description">{t('serviceOrders.form.description')}</Label>
            <textarea
              id="so-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('serviceOrders.form.descriptionPlaceholder')}
              maxLength={2000}
              rows={4}
              className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="so-scheduled">{t('serviceOrders.form.scheduled')}</Label>
              <Input
                id="so-scheduled"
                type="datetime-local"
                value={scheduledLocal}
                onChange={(e) => setScheduledLocal(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="so-cost">{t('serviceOrders.form.cost')}</Label>
              <Input
                id="so-cost"
                type="number"
                min="0"
                step="0.01"
                value={cost}
                onChange={(e) => setCost(e.target.value)}
                placeholder={t('serviceOrders.form.costPlaceholder')}
              />
            </div>
          </div>

          {validationError && <p className="text-sm text-destructive">{validationError}</p>}
          {submitError && <p className="text-sm text-destructive">{submitError}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={isSubmitting}>
              {t('common.cancel')}
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isSubmitting
                ? t('serviceOrders.form.submitting')
                : isEdit
                  ? t('common.save')
                  : t('serviceOrders.form.submit')}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
