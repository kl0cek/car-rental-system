'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useTranslation } from '@/i18n/useTranslation';
import type { MaintenancePeriod } from '@/hooks/useUpdateVehicleStatus';

interface MaintenanceFormProps {
  isLoading: boolean;
  onSubmit: (period: MaintenancePeriod) => void;
  onCancel: () => void;
}

export function MaintenanceForm({ isLoading, onSubmit, onCancel }: MaintenanceFormProps) {
  const { t } = useTranslation();
  const today = new Date().toISOString().slice(0, 10);
  const [startDate, setStartDate] = useState(today);
  const [endDate, setEndDate] = useState('');
  const [notes, setNotes] = useState('');

  const isValid = startDate && endDate && endDate >= startDate;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isValid) return;
    onSubmit({ startDate, endDate, notes: notes.trim() || undefined });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3 p-4 bg-secondary/40 rounded-lg">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="m-start">{t('maintenance.startDate')}</Label>
          <Input
            id="m-start"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            min={today}
            required
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="m-end">{t('maintenance.endDate')}</Label>
          <Input
            id="m-end"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={startDate || today}
            required
          />
        </div>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="m-notes">{t('maintenance.notes')}</Label>
        <textarea
          id="m-notes"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder={t('maintenance.notesPlaceholder')}
          rows={3}
          className="w-full text-sm rounded-md border border-input bg-background px-3 py-2 focus-visible:outline-hidden focus-visible:ring-1 focus-visible:ring-ring"
        />
      </div>
      <div className="flex gap-2 justify-end">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={isLoading}>
          {t('common.cancel')}
        </Button>
        <Button type="submit" size="sm" disabled={!isValid || isLoading}>
          {isLoading ? t('maintenance.submitting') : t('maintenance.submit')}
        </Button>
      </div>
    </form>
  );
}
