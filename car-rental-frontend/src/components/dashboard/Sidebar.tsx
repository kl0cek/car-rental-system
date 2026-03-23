'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Car, LogOut } from 'lucide-react';
import { cn } from '@/lib/utils';
import { navigation, secondaryNavigation } from '@/data/dashboard/constants';
import { useAuth } from '@/contexts/AuthContext';

const STAFF_ROLES = ['employee', 'technician', 'admin'] as const;

export default function DashboardSidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const isStaff = user ? STAFF_ROLES.includes(user.role as (typeof STAFF_ROLES)[number]) : false;
  const filteredNavigation = navigation.filter((item) => !item.staffOnly || isStaff);

  return (
    <aside className="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
      <div className="flex flex-col grow bg-card border-r border-border">
        <div className="flex items-center gap-3 px-6 py-5 border-b border-border">
          <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
            <Car className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-foreground">DriveEase</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {filteredNavigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                pathname === item.href
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-border space-y-1">
          {secondaryNavigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
            >
              <item.icon className="w-5 h-5" />
              {item.name}
            </Link>
          ))}
          <button
            onClick={async () => {
              await logout();
              window.location.href = '/';
            }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-destructive hover:bg-destructive/10 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Sign out
          </button>
        </div>

        {user && (
          <div className="px-3 py-4 border-t border-border">
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center">
                <span className="text-sm font-medium text-secondary-foreground">
                  {user.firstName[0]}{user.lastName[0]}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">
                  {user.firstName} {user.lastName}
                </p>
                <p className="text-xs text-muted-foreground truncate">{user.email}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
