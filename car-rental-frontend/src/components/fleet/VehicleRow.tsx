import { Car, ExternalLink, MoreHorizontal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TableCell, TableRow } from '@/components/ui/table';
import { STATUS_CONFIG, ENGINE_CONFIG, CATEGORY_LABELS } from '@/data/vehicles/constants';
import type { Vehicle } from '@/types/vehicle';

export function VehicleRow({ vehicle: v }: { vehicle: Vehicle }) {
  const status = STATUS_CONFIG[v.status];
  const engine = ENGINE_CONFIG[v.engineType];
  const EngineIcon = engine.Icon;

  return (
    <TableRow>
      <TableCell className="px-4 py-3">
        <div className="w-10 h-10 rounded-md bg-muted overflow-hidden shrink-0 flex items-center justify-center">
          {v.imageUrl ? (
            <img src={v.imageUrl} alt="" className="w-full h-full object-cover" />
          ) : (
            <Car className="w-5 h-5 text-muted-foreground/40" />
          )}
        </div>
      </TableCell>

      <TableCell className="px-4 py-3">
        <p className="font-medium text-foreground">{v.brand} {v.model}</p>
        <p className="text-xs text-muted-foreground">{v.color} · {v.seats} seats</p>
      </TableCell>

      <TableCell className="px-4 py-3 text-foreground">{v.year}</TableCell>

      <TableCell className="px-4 py-3 text-foreground">
        {v.mileage.toLocaleString()} km
      </TableCell>

      <TableCell className="px-4 py-3 font-medium text-foreground">
        {v.dailyBasePrice.toFixed(0)} PLN
      </TableCell>

      <TableCell className="px-4 py-3">
        <Badge variant="secondary" className="text-xs">
          {CATEGORY_LABELS[v.category.name]}
        </Badge>
      </TableCell>

      <TableCell className="px-4 py-3">
        <span className="flex items-center gap-1 text-sm text-muted-foreground">
          <EngineIcon className="w-3.5 h-3.5" />
          {engine.label}
        </span>
      </TableCell>

      <TableCell className="px-4 py-3 text-sm font-mono text-muted-foreground">
        {v.licensePlate}
      </TableCell>

      <TableCell className="px-4 py-3">
        <Badge className={status.className}>{status.label}</Badge>
      </TableCell>

      <TableCell className="px-4 py-3 text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem disabled>
              <ExternalLink className="w-4 h-4 mr-2" />
              View details
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}
