import { Users } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { CustomerRow } from './CustomerRow';
import type { Customer } from '@/types/customer';

const COLS = ['Customer', 'Email', 'Phone', 'Reservations', 'Joined', 'Status', 'Actions'];

interface CustomerTableProps {
  customers: Customer[];
  isLoading: boolean;
  emptyMessage?: string;
}

export function CustomerTable({ customers, isLoading, emptyMessage }: CustomerTableProps) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-full bg-secondary flex items-center justify-center mb-3">
          <Users className="w-7 h-7 text-muted-foreground" />
        </div>
        <p className="font-medium text-foreground">No customers found</p>
        {emptyMessage && <p className="text-sm text-muted-foreground mt-1">{emptyMessage}</p>}
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {COLS.map((col) => (
            <TableHead
              key={col}
              className={`px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground ${col === 'Actions' ? 'text-right' : ''}`}
            >
              {col}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {customers.map((c) => (
          <CustomerRow key={c.id} customer={c} />
        ))}
      </TableBody>
    </Table>
  );
}
