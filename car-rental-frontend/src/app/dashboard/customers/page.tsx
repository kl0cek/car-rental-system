'use client';

import { useState } from 'react';
import { Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { CustomerTable } from '@/components/customers/CustomerTable';
import { useCustomers } from '@/hooks/useCustomers';

export default function CustomersPage() {
  const [search, setSearch] = useState('');
  const { customers, isLoading } = useCustomers();

  const filtered = customers.filter((c) => {
    const q = search.toLowerCase();
    return (
      c.firstName.toLowerCase().includes(q) ||
      c.lastName.toLowerCase().includes(q) ||
      c.email.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Customers</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {isLoading
              ? 'Loading...'
              : `${filtered.length} customer${filtered.length !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by name or email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      <Card>
        <CardContent className="p-0 overflow-x-auto">
          <CustomerTable
            customers={filtered}
            isLoading={isLoading}
            emptyMessage={search ? `No results for "${search}"` : undefined}
          />
        </CardContent>
      </Card>
    </div>
  );
}
