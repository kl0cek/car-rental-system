import { Car } from 'lucide-react';
import React from 'react';

const stats = [
  { value: '500+', label: 'Vehicles' },
  { value: '12k+', label: 'Bookings' },
  { value: '98%', label: 'Satisfaction' },
];

export function BrandingSidebar() {
  return (
    <div className="hidden lg:flex lg:w-1/2 bg-primary relative overflow-hidden">
      <div className="absolute inset-0 bg-linear-to-br from-primary to-primary/80" />

      <div className="relative z-10 flex flex-col justify-between p-12 text-primary-foreground">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-foreground/20 rounded-lg flex items-center justify-center">
            <Car className="w-6 h-6" />
          </div>
          <span className="text-xl font-semibold tracking-tight">DriveEase</span>
        </div>

        <div className="space-y-6">
          <h1 className="text-4xl font-bold leading-tight text-balance">
            Manage your fleet with confidence
          </h1>
          <p className="text-primary-foreground/80 text-lg leading-relaxed max-w-md">
            Streamline your car rental operations with our intuitive booking management system.
          </p>
        </div>

        <div className="flex flex-row items-center gap-8">
          {stats.map((stat, i) => (
            <React.Fragment key={stat.label}>
              {i > 0 && <div key={`divider-${i}`} className="w-px h-12 bg-primary-foreground/20" />}
              <div key={stat.label}>
                <p className="text-3xl font-bold">{stat.value}</p>
                <p className="text-primary-foreground/70 text-sm">{stat.label}</p>
              </div>
            </React.Fragment>
          ))}
        </div>
      </div>

      <div className="absolute -bottom-20 -right-20 w-80 h-80 bg-primary-foreground/10 rounded-full blur-3xl" />
      <div className="absolute top-20 -right-10 w-40 h-40 bg-accent/20 rounded-full blur-2xl" />
    </div>
  );
}
