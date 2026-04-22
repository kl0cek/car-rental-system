'use client';

import Link from 'next/link';
import { Plus } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { isStaffRole } from '@/data/dashboard/constants';

export function DashboardPageHeader() {
  const { user } = useAuth();
  const isStaff = isStaffRole(user?.role);

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Welcome back! Here&apos;s your rental overview.
        </p>
      </div>
      {!isStaff && (
        <Link
          href="/dashboard/bookings/new"
          className="inline-flex items-center justify-center gap-2 h-10 px-4 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Booking
        </Link>
      )}
    </div>
  );
}
