'use client';

import { Car, ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { SORTABLE_COLS } from '@/data/vehicles/constants';
import { VehicleRow } from './VehicleRow';
import type { Vehicle, SortableField } from '@/types/vehicle';

interface SortState {
  sortBy: SortableField;
  sortOrder: 'asc' | 'desc';
}

interface FleetTableProps {
  vehicles: Vehicle[];
  isLoading: boolean;
  sort: SortState;
  onSortChange: (sortBy: SortableField) => void;
}

const SortIcon = ({ field, sort }: { field: SortableField; sort: SortState }) =>
  sort.sortBy !== field ? (
    <ChevronsUpDown className="w-3.5 h-3.5 ml-1 opacity-40" />
  ) : sort.sortOrder === 'asc' ? (
    <ChevronUp className="w-3.5 h-3.5 ml-1" />
  ) : (
    <ChevronDown className="w-3.5 h-3.5 ml-1" />
  );

export function FleetTable({ vehicles, isLoading, sort, onSortChange }: FleetTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2 p-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (vehicles.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-full bg-secondary flex items-center justify-center mb-3">
          <Car className="w-7 h-7 text-muted-foreground" />
        </div>
        <p className="font-medium text-foreground">No vehicles found</p>
        <p className="text-sm text-muted-foreground mt-1">Try a different status filter</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-12 px-4" />
          {SORTABLE_COLS.map(({ label, field }) => (
            <TableHead key={field} className="px-4">
              <button
                onClick={() => onSortChange(field)}
                className="flex items-center text-xs uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
              >
                {label}
                <SortIcon field={field} sort={sort} />
              </button>
            </TableHead>
          ))}
          {['Category', 'Engine', 'Plate', 'Status'].map((col) => (
            <TableHead
              key={col}
              className="px-4 text-xs uppercase tracking-wider text-muted-foreground"
            >
              {col}
            </TableHead>
          ))}
          <TableHead className="px-4 text-right text-xs uppercase tracking-wider text-muted-foreground">
            Actions
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((v) => (
          <VehicleRow key={v.id} vehicle={v} />
        ))}
      </TableBody>
    </Table>
  );
}
