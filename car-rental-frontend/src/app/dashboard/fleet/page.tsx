'use client';

import { useCallback, useState } from 'react';
import { Car } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { FleetStatusTabs } from '@/components/fleet/FleetStatusTabs';
import { FleetTable } from '@/components/fleet/FleetTable';
import { VehiclePagination } from '@/components/vehicles/VehiclePagination';
import { useFleetVehicles, type FleetParams } from '@/hooks/useFleetVehicles';
import type { VehicleStatus, SortableField } from '@/types/vehicle';

const DEFAULT_PARAMS: FleetParams = {
  status: null,
  page: 1,
  sortBy: 'brand',
  sortOrder: 'asc',
};

export default function FleetPage() {
  const [params, setParams] = useState<FleetParams>(DEFAULT_PARAMS);

  const update = useCallback((patch: Partial<FleetParams>) => {
    setParams((prev) => ({ ...prev, ...patch, page: 'page' in patch ? (patch.page ?? 1) : 1 }));
  }, []);

  const handleStatusChange = (status: VehicleStatus | null) => update({ status });

  const handleSortChange = (sortBy: SortableField) => {
    setParams((prev) => ({
      ...prev,
      sortBy,
      sortOrder: prev.sortBy === sortBy && prev.sortOrder === 'asc' ? 'desc' : 'asc',
      page: 1,
    }));
  };

  const { vehicles, total, totalPages, isLoading } = useFleetVehicles(params);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Fleet Management</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isLoading ? 'Loading...' : `${total} vehicle${total !== 1 ? 's' : ''} total`}
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Car className="w-4 h-4" />
          <span>Staff only</span>
        </div>
      </div>

      <FleetStatusTabs value={params.status} onChange={handleStatusChange} />

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <FleetTable
            vehicles={vehicles}
            isLoading={isLoading}
            sort={{ sortBy: params.sortBy, sortOrder: params.sortOrder }}
            onSortChange={handleSortChange}
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
