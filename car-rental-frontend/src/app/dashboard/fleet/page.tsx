'use client';

import { useCallback, useEffect, useState } from 'react';
import { Car } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { FleetStatusTabs } from '@/components/fleet/FleetStatusTabs';
import { FleetTable } from '@/components/fleet/FleetTable';
import { FleetToolbar } from '@/components/fleet/FleetToolbar';
import { FleetBulkActionBar } from '@/components/fleet/FleetBulkActionBar';
import { VehiclePagination } from '@/components/vehicles/VehiclePagination';
import { VehicleDetailPanel } from '@/components/vehicles/DetailPanel/VehicleDetailPanel';
import { useFleetVehicles, type FleetParams } from '@/hooks/useFleetVehicles';
import { useBulkUpdateVehicleStatus } from '@/hooks/useBulkUpdateVehicleStatus';
import type { SortableField, Vehicle, VehicleStatus, PaginatedVehiclesApi } from '@/types/vehicle';
import { mapVehicle } from '@/types/vehicle';
import { useTranslation } from '@/i18n/useTranslation';
import { useAuth } from '@/contexts/AuthContext';
import { buildCsv, downloadCsv } from '@/lib/csv';

const DEFAULT_PARAMS: FleetParams = {
  status: null,
  page: 1,
  sortBy: 'brand',
  sortOrder: 'asc',
  search: '',
  engineType: null,
  category: null,
};

// Debounce search input so each keystroke doesn't fire its own request.
function useDebouncedValue<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const handle = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(handle);
  }, [value, delay]);
  return debounced;
}

export default function FleetPage() {
  const [params, setParams] = useState<FleetParams>(DEFAULT_PARAMS);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [detailVehicle, setDetailVehicle] = useState<Vehicle | null>(null);
  const [exporting, setExporting] = useState(false);
  const [searchInput, setSearchInput] = useState('');
  const debouncedSearch = useDebouncedValue(searchInput, 300);
  const { t } = useTranslation();
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  // Sync the debounced query into the actual fetch params (resetting page to 1)
  useEffect(() => {
    setParams((prev) =>
      prev.search === debouncedSearch ? prev : { ...prev, search: debouncedSearch, page: 1 }
    );
  }, [debouncedSearch]);

  const update = useCallback((patch: Partial<FleetParams>) => {
    setParams((prev) => ({ ...prev, ...patch, page: 'page' in patch ? (patch.page ?? 1) : 1 }));
  }, []);

  const handleSortChange = (sortBy: SortableField) => {
    setParams((prev) => ({
      ...prev,
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'asc' ? 'desc' : 'asc',
      page: 1,
    }));
  };

  const { vehicles, total, totalPages, isLoading, refresh } = useFleetVehicles(params);
  const { bulkUpdate, isLoading: bulkLoading, error: bulkError } = useBulkUpdateVehicleStatus();

  const toggleRow = (id: string, selected: boolean) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (selected) next.add(id);
      else next.delete(id);
      return next;
    });
  };

  const toggleAll = (selected: boolean) => {
    setSelectedIds(selected ? new Set(vehicles.map((v) => v.id)) : new Set());
  };

  const clearSelection = () => setSelectedIds(new Set());

  const applyBulkStatus = async (status: VehicleStatus) => {
    const ids = Array.from(selectedIds);
    try {
      await bulkUpdate(ids, status);
      clearSelection();
      await refresh();
    } catch (err) {
      // Surface the error via the bar — keep the selection so the user can retry.
      console.error('Bulk status update failed', err);
    }
  };

  // CSV export — pulls up to 1000 rows respecting the current filter set so
  // operators get the slice they're actually looking at, not the whole DB.
  const handleExport = async () => {
    setExporting(true);
    try {
      const search = new URLSearchParams();
      search.set('limit', '1000');
      search.set('offset', '0');
      search.set('sort_by', params.sortBy);
      search.set('sort_order', params.sortOrder);
      if (params.status) search.set('status', params.status);
      if (params.search) search.set('search', params.search);
      if (params.engineType) search.set('engine_type', params.engineType);
      if (params.category) search.set('category', params.category);
      const res = await fetch(`/api/vehicles?${search.toString()}`, { credentials: 'include' });
      if (!res.ok) throw new Error('Export failed');
      const data = (await res.json()) as PaginatedVehiclesApi;
      const rows = data.items.map(mapVehicle);

      const csv = buildCsv(
        [
          'Brand',
          'Model',
          'Year',
          'License plate',
          'Color',
          'Category',
          'Engine',
          'Horsepower',
          'Seats',
          'Mileage (km)',
          'Daily price (PLN)',
          'Status',
        ],
        rows.map((v) => [
          v.brand,
          v.model,
          v.year,
          v.licensePlate,
          v.color,
          v.category.name,
          v.engineType,
          v.horsepower,
          v.seats,
          v.mileage,
          v.dailyBasePrice.toFixed(2),
          v.status,
        ])
      );
      downloadCsv(`fleet-${new Date().toISOString().slice(0, 10)}.csv`, csv);
    } catch (err) {
      console.error('Export failed', err);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-5">
      {detailVehicle && (
        <VehicleDetailPanel
          vehicle={detailVehicle}
          onClose={() => setDetailVehicle(null)}
          mode="staff"
        />
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t('fleet.title')}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isLoading
              ? t('common.loading')
              : t(total === 1 ? 'fleet.vehicleCount' : 'fleet.vehicleCountPlural', {
                  count: total,
                })}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Car className="w-4 h-4" />
          <span>{t('common.staffOnly')}</span>
        </div>
      </div>

      <FleetToolbar
        search={searchInput}
        onSearchChange={setSearchInput}
        engineType={params.engineType ?? null}
        onEngineTypeChange={(engineType) => update({ engineType })}
        category={params.category ?? null}
        onCategoryChange={(category) => update({ category })}
        onExport={handleExport}
        exporting={exporting}
      />

      <FleetStatusTabs value={params.status} onChange={(status) => update({ status })} />

      <FleetBulkActionBar
        selectedCount={selectedIds.size}
        onClear={clearSelection}
        onApplyStatus={applyBulkStatus}
        isLoading={bulkLoading}
      />
      {bulkError && <p className="text-sm text-red-600 dark:text-red-400">{bulkError}</p>}

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <FleetTable
            vehicles={vehicles}
            isLoading={isLoading}
            sort={{ sortBy: params.sortBy, sortOrder: params.sortOrder }}
            onSortChange={handleSortChange}
            selectedIds={selectedIds}
            onToggleRow={toggleRow}
            onToggleAll={toggleAll}
            onViewDetails={setDetailVehicle}
            canEdit={isAdmin}
            buildEditHref={(id) => `/dashboard/admin/vehicles/${id}/edit`}
          />
        </CardContent>
      </Card>

      {totalPages > 1 && (
        <VehiclePagination
          currentPage={params.page}
          totalPages={totalPages}
          onPageChange={(page) => update({ page })}
        />
      )}
    </div>
  );
}
