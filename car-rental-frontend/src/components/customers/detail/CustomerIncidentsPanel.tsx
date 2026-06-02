'use client';

import { useState } from 'react';
import { AlertOctagon, Plus, Trash2, X, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
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
import { formatDate } from '@/lib/formatters';
import { useCustomerIncidentMutations } from '@/hooks/customers/useCustomerDetail';
import type {
  CustomerRentalSummary,
  Incident,
  IncidentSeverity,
  IncidentType,
} from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';

interface CustomerIncidentsPanelProps {
  customerId: string;
  incidents: Incident[];
  rentals: CustomerRentalSummary[];
  onChanged: () => void;
}

const TYPES: IncidentType[] = ['damage', 'late_return', 'traffic_violation', 'complaint', 'other'];
const SEVERITIES: IncidentSeverity[] = ['minor', 'moderate', 'major'];

const SEVERITY_TONE: Record<IncidentSeverity, string> = {
  minor: 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300',
  moderate: 'bg-yellow-500/15 text-yellow-700 dark:text-yellow-300',
  major: 'bg-destructive/10 text-destructive',
};

const NO_RENTAL = '__none__';

export function CustomerIncidentsPanel({
  customerId,
  incidents,
  rentals,
  onChanged,
}: CustomerIncidentsPanelProps) {
  const { t } = useTranslation();
  const { createIncident, deleteIncident, isLoading } = useCustomerIncidentMutations(customerId);
  const [adding, setAdding] = useState(false);
  const [type, setType] = useState<IncidentType>('damage');
  const [severity, setSeverity] = useState<IncidentSeverity>('moderate');
  const [rentalId, setRentalId] = useState<string>(NO_RENTAL);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [cost, setCost] = useState('');
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setAdding(false);
    setType('damage');
    setSeverity('moderate');
    setRentalId(NO_RENTAL);
    setTitle('');
    setDescription('');
    setCost('');
    setError(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createIncident({
        rentalId: rentalId === NO_RENTAL ? null : rentalId,
        type,
        severity,
        title,
        description,
        cost: cost.trim() === '' ? null : cost.trim(),
      });
      onChanged();
      reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add incident');
    }
  }

  async function remove(id: string) {
    try {
      await deleteIncident(id);
      onChanged();
    } catch (err) {
      console.error('Delete incident failed', err);
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between space-y-0">
        <CardTitle className="text-base flex items-center gap-2">
          <AlertOctagon className="w-4 h-4" />
          {t('customerDetail.incidents')}
        </CardTitle>
        {!adding && (
          <Button size="sm" variant="outline" onClick={() => setAdding(true)}>
            <Plus className="w-3.5 h-3.5 mr-1" />
            {t('customerDetail.addIncident')}
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        {adding && (
          <form
            onSubmit={submit}
            className="rounded-lg border border-border p-3 space-y-3 bg-muted/30"
          >
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>{t('customerDetail.incidentType')}</Label>
                <Select value={type} onValueChange={(v: string) => setType(v as IncidentType)}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {TYPES.map((tp) => (
                      <SelectItem key={tp} value={tp}>
                        {t(`customerDetail.incidentType.${tp}` as TranslationKey)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>{t('customerDetail.severity')}</Label>
                <Select
                  value={severity}
                  onValueChange={(v: string) => setSeverity(v as IncidentSeverity)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SEVERITIES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {t(`customerDetail.severity.${s}` as TranslationKey)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {rentals.length > 0 && (
                <div className="sm:col-span-2 space-y-1.5">
                  <Label>{t('customerDetail.linkedRental')}</Label>
                  <Select value={rentalId} onValueChange={setRentalId}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value={NO_RENTAL}>—</SelectItem>
                      {rentals.map((r) => (
                        <SelectItem key={r.id} value={r.id}>
                          {r.vehicleName} ({formatDate(r.pickupDate)})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              <div className="sm:col-span-2 space-y-1.5">
                <Label htmlFor="incident-cost">{t('customerDetail.cost')}</Label>
                <Input
                  id="incident-cost"
                  type="number"
                  inputMode="decimal"
                  min="0"
                  step="0.01"
                  value={cost}
                  onChange={(e) => setCost(e.target.value)}
                  placeholder="0.00"
                />
              </div>
              <div className="sm:col-span-2 space-y-1.5">
                <Label htmlFor="incident-title">{t('customerDetail.incidentTitle')}</Label>
                <Input
                  id="incident-title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  required
                  maxLength={200}
                />
              </div>
              <div className="sm:col-span-2 space-y-1.5">
                <Label htmlFor="incident-desc">{t('customerDetail.description')}</Label>
                <textarea
                  id="incident-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  maxLength={2000}
                  rows={3}
                  className="w-full rounded-lg border border-input bg-transparent px-3 py-2 text-sm focus-visible:ring-3 focus-visible:ring-ring/50 outline-none resize-none"
                />
              </div>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex gap-2 justify-end">
              <Button type="button" variant="ghost" size="sm" onClick={reset}>
                <X className="w-3.5 h-3.5 mr-1" />
                {t('common.cancel')}
              </Button>
              <Button type="submit" size="sm" disabled={isLoading}>
                {isLoading && <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" />}
                {t('common.save')}
              </Button>
            </div>
          </form>
        )}

        {incidents.length === 0 ? (
          <p className="text-sm text-muted-foreground py-6 text-center">
            {t('customerDetail.noIncidents')}
          </p>
        ) : (
          <ul className="space-y-2">
            {incidents.map((incident) => (
              <li key={incident.id} className="rounded-lg border border-border p-3 space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm">{incident.title}</span>
                      <Badge className={SEVERITY_TONE[incident.severity]}>
                        {t(`customerDetail.severity.${incident.severity}` as TranslationKey)}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {t(`customerDetail.incidentType.${incident.type}` as TranslationKey)}
                      </Badge>
                      {incident.cost !== null && (
                        <Badge variant="outline" className="text-xs">
                          {incident.cost} PLN
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {incident.reportedBy.firstName} {incident.reportedBy.lastName} ·{' '}
                      {formatDate(incident.createdAt)}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(incident.id)}
                    aria-label={t('common.delete')}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </Button>
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {incident.description}
                </p>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
