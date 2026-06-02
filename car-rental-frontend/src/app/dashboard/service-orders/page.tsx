'use client';

import { useMemo, useState } from 'react';
import { Wrench, AlertTriangle, Plus } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useTranslation } from '@/i18n/useTranslation';
import { ServiceOrderStatsCards } from '@/components/service-orders/ServiceOrderStatsCards';
import { ServiceOrderTable } from '@/components/service-orders/ServiceOrderTable';
import { ServiceOrderFormModal } from '@/components/service-orders/ServiceOrderFormModal';
import { useServiceOrders } from '@/hooks/service-orders/useServiceOrders';
import type { ServiceOrder, ServiceOrderStatus } from '@/types/serviceOrder';

const ALLOWED_ROLES = new Set(['technician', 'admin']);
type Tab = 'all' | ServiceOrderStatus;

const TABS: Array<{ id: Tab; labelKey: 'serviceOrders.tab.all' | 'serviceOrders.tab.scheduled' | 'serviceOrders.tab.inProgress' | 'serviceOrders.tab.completed' }> = [
  { id: 'all', labelKey: 'serviceOrders.tab.all' },
  { id: 'scheduled', labelKey: 'serviceOrders.tab.scheduled' },
  { id: 'in_progress', labelKey: 'serviceOrders.tab.inProgress' },
  { id: 'completed', labelKey: 'serviceOrders.tab.completed' },
];

export default function ServiceOrdersPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { t } = useTranslation();

  const [tab, setTab] = useState<Tab>('scheduled');
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<ServiceOrder | undefined>(undefined);

  const statusFilter = tab === 'all' ? undefined : tab;
  const { data, isLoading } = useServiceOrders({ status: statusFilter, limit: 50 });

  const items = useMemo(() => data?.items ?? [], [data]);

  if (authLoading) {
    return <p className="text-sm text-muted-foreground">{t('common.loading')}</p>;
  }
  if (!user || !ALLOWED_ROLES.has(user.role)) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="w-4 h-4" />
        <AlertDescription>{t('common.staffOnly')}</AlertDescription>
      </Alert>
    );
  }

  const handleOpenCreate = () => {
    setEditing(undefined);
    setFormOpen(true);
  };

  const handleOpenEdit = (order: ServiceOrder) => {
    setEditing(order);
    setFormOpen(true);
  };

  const emptyKey =
    tab === 'scheduled'
      ? 'serviceOrders.empty.scheduled'
      : tab === 'in_progress'
        ? 'serviceOrders.empty.inProgress'
        : tab === 'completed'
          ? 'serviceOrders.empty.completed'
          : 'serviceOrders.empty.all';

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
            <Wrench className="w-5 h-5 text-foreground" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              {t('serviceOrders.title')}
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {t('serviceOrders.subtitle')}
            </p>
          </div>
        </div>
        <Button onClick={handleOpenCreate}>
          <Plus className="w-4 h-4" />
          {t('serviceOrders.action.create')}
        </Button>
      </div>

      <ServiceOrderStatsCards />

      <div className="flex gap-1 flex-wrap">
        {TABS.map((it) => (
          <button
            key={it.id}
            onClick={() => setTab(it.id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
              tab === it.id
                ? 'bg-primary text-primary-foreground border-primary'
                : 'border-border text-muted-foreground hover:bg-secondary hover:text-foreground'
            }`}
          >
            {t(it.labelKey)}
          </button>
        ))}
      </div>

      <Card>
        <CardHeader className="border-b pb-4">
          <CardTitle>{t('serviceOrders.list.title')}</CardTitle>
          <CardDescription>{t('serviceOrders.list.description')}</CardDescription>
        </CardHeader>
        <CardContent className="p-0 overflow-x-auto">
          <ServiceOrderTable
            orders={items}
            isLoading={isLoading}
            emptyMessage={t(emptyKey)}
            onEdit={handleOpenEdit}
          />
        </CardContent>
      </Card>

      {formOpen && (
        <ServiceOrderFormModal
          order={editing}
          onClose={() => setFormOpen(false)}
        />
      )}
    </div>
  );
}
