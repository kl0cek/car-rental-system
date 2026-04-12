'use client';

import { useCallback, useState } from 'react';
import { Car } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { VehicleCard } from '@/components/vehicles/VehicleCard';
import { VehicleFilters, type FiltersState } from '@/components/vehicles/VehicleFilters';
import { VehiclePagination } from '@/components/vehicles/VehiclePagination';
import { VehiclesHeader } from '@/components/vehicles/VehiclesHeader';
import { useVehicles } from '@/hooks/useVehicles';
import { PRICE_MIN, PRICE_MAX, YEAR_MIN, YEAR_MAX, PAGE_SIZE } from '@/types/vehicle';

const DEFAULT_FILTERS: FiltersState & { page: number } = {
  category: null,
  engineType: null,
  priceRange: [PRICE_MIN, PRICE_MAX],
  yearRange: [YEAR_MIN, YEAR_MAX],
  minSeats: null,
  availableFrom: '',
  availableTo: '',
  sortBy: 'created_at',
  sortOrder: 'desc',
  page: 1,
};

export default function VehiclesPage() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const updateFilters = useCallback((updates: Partial<typeof DEFAULT_FILTERS>) => {
    setFilters((prev) => ({
      ...prev,
      ...updates,
      page: 'page' in updates ? (updates.page ?? 1) : 1,
    }));
  }, []);

  const { vehicles, total, isLoading } = useVehicles(filters);
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-5">
      <VehiclesHeader
        total={total}
        isLoading={isLoading}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen((v) => !v)}
      />

      <div className="flex gap-6 items-start">
        <aside
          className={`${
            sidebarOpen ? 'block' : 'hidden'
          } lg:block w-60 shrink-0 bg-card rounded-xl border border-border p-4 sticky top-4`}
        >
          <VehicleFilters filters={filters} onChange={updateFilters} />
        </aside>

        <div className="flex-1 min-w-0 space-y-4">
          {isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-90 rounded-xl" />
              ))}
            </div>
          ) : vehicles.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center mb-4">
                <Car className="w-8 h-8 text-muted-foreground" />
              </div>
              <p className="font-semibold text-foreground">No vehicles found</p>
              <p className="text-sm text-muted-foreground mt-1">
                Try adjusting or clearing your filters
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
              {vehicles.map((vehicle) => (
                <VehicleCard key={vehicle.id} vehicle={vehicle} />
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <VehiclePagination
              currentPage={filters.page}
              totalPages={totalPages}
              onPageChange={(page) => updateFilters({ page })}
            />
          )}
        </div>
      </div>
    </div>
  );
}
