import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import type { dashboardMockData } from '@/data/dashboard/dashboardData';

interface StatsGridProps {
  data: typeof dashboardMockData;
}

export function StatsGrid({ data }: StatsGridProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {data.map((stat) => (
        <div
          key={stat.name}
          className="bg-card rounded-xl border border-border p-5 hover:shadow-sm transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center">
              <stat.icon className="w-5 h-5 text-foreground" />
            </div>
            <div
              className={`flex items-center gap-1 text-xs font-medium ${
                stat.trend === 'up' ? 'text-green-400' : 'text-destructive'
              }`}
            >
              {stat.change}
              {stat.trend === 'up' ? (
                <ArrowUpRight className="w-3 h-3" />
              ) : (
                <ArrowDownRight className="w-3 h-3" />
              )}
            </div>
          </div>
          <div className="mt-4">
            <p className="text-2xl font-semibold text-foreground">{stat.value}</p>
            <p className="text-sm text-muted-foreground mt-1">{stat.name}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
