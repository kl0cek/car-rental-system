'use client';

import { useState } from 'react';
import { Search, Bell, Menu, X, Car, LogOut } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { getFilteredNavigation } from '@/data/dashboard/constants';
import { useAuth } from '@/contexts/AuthContext';

export default function DashboardHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const filteredNavigation = getFilteredNavigation(user?.role);

  return (
    <>
      <header className="sticky top-0 z-40 bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="flex items-center justify-between h-16 px-6">
          <button
            type="button"
            aria-label="Open menu"
            className="lg:hidden -ml-2 p-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
            onClick={() => setMobileMenuOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex-1 max-w-md mx-4 lg:mx-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="search"
                placeholder="Search bookings, customers..."
                className="w-full h-10 pl-10 pr-4 rounded-lg border border-input bg-background text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              aria-label="Notifications"
              className="relative p-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-accent rounded-full" />
            </button>
            <div className="hidden sm:flex items-center gap-3 pl-3 border-l border-border">
              <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
                <span className="text-xs font-medium text-secondary-foreground">
                  {user ? `${user.firstName[0]}${user.lastName[0]}` : '??'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-foreground/20 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="fixed inset-y-0 left-0 w-72 bg-card shadow-xl">
            <div className="flex items-center justify-between px-6 py-5 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center">
                  <Car className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="text-lg font-semibold text-foreground">DriveEase</span>
              </div>
              <button
                type="button"
                aria-label="Close menu"
                className="p-2 -mr-2 rounded-lg text-muted-foreground hover:bg-secondary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <nav className="px-3 py-4 space-y-1">
              {filteredNavigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
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

            <div className="absolute bottom-0 left-0 right-0 px-3 py-4 border-t border-border">
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
          </div>
        </div>
      )}
    </>
  );
}
