import { Clock, ChevronRight } from 'lucide-react';
import type { Return } from '@/types/dashboard/booking';
import { mockReturns } from '@/data/dashboard/mockReturns';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface UpcomingReturnsProps {
  returns?: Return[];
}

export default function UpcomingReturns({ returns = mockReturns }: UpcomingReturnsProps) {
  return (
    <Card className="h-full">
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Upcoming Returns</CardTitle>
            <CardDescription className="mt-0.5">Vehicles due for return</CardDescription>
          </div>
          <div className="w-8 h-8 rounded-lg bg-secondary flex items-center justify-center">
            <Clock className="w-4 h-4 text-foreground" />
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {returns.map((item) => (
            <button
              key={item.id}
              className="w-full flex items-center gap-3 p-4 hover:bg-secondary/50 transition-colors text-left"
            >
              <div
                className={`w-2 h-2 rounded-full shrink-0 ${item.urgent ? 'bg-destructive' : 'bg-accent'}`}
              />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{item.customer}</p>
                <p className="text-sm text-muted-foreground truncate">{item.car}</p>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">{item.returnTime}</span>
                  <span className="text-xs text-muted-foreground">•</span>
                  <span className="text-xs text-muted-foreground truncate">{item.location}</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-border">
          <Button variant="link" className="w-full text-sm p-0 h-auto">
            View all returns
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
