'use client';

import { Car, ExternalLink, MoreHorizontal, Pencil } from 'lucide-react';
import Link from 'next/link';
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
import { useTranslation } from '@/i18n/useTranslation';
import type { TranslationKey } from '@/i18n/translations';
import Image from 'next/image';

interface VehicleRowProps {
  vehicle: Vehicle;
  selected: boolean;
  onSelectChange: (id: string, selected: boolean) => void;
  onViewDetails: (vehicle: Vehicle) => void;
  /** Edit link target — falls back to admin form if undefined. */
  editHref?: string;
  /** Whether the current user can edit (admin only). Hides the link otherwise. */
  canEdit: boolean;
}

export function VehicleRow({
  vehicle: v,
  selected,
  onSelectChange,
  onViewDetails,
  editHref,
  canEdit,
}: VehicleRowProps) {
  const { t } = useTranslation();
  const status = STATUS_CONFIG[v.status];
  const engine = ENGINE_CONFIG[v.engineType];
  const EngineIcon = engine.Icon;

  return (
    <TableRow data-state={selected ? 'selected' : undefined}>
      <TableCell className="px-3 py-3 w-10">
        <input
          type="checkbox"
          checked={selected}
          onChange={(e) => onSelectChange(v.id, e.target.checked)}
          className="w-4 h-4 rounded border-input cursor-pointer"
          aria-label={`Select ${v.brand} ${v.model}`}
        />
      </TableCell>

      <TableCell className="px-4 py-3">
        <button
          type="button"
          onClick={() => onViewDetails(v)}
          className="w-10 h-10 rounded-md bg-muted overflow-hidden shrink-0 flex items-center justify-center hover:opacity-80 transition-opacity"
          aria-label={t('vehicles.viewDetails')}
        >
          {v.imageUrl ? (
            <Image
              src={v.imageUrl}
              alt=""
              width={40}
              height={40}
              className="w-full h-full object-cover"
            />
          ) : (
            <Car className="w-5 h-5 text-muted-foreground/40" />
          )}
        </button>
      </TableCell>

      <TableCell className="px-4 py-3">
        <button
          type="button"
          onClick={() => onViewDetails(v)}
          className="text-left hover:underline"
        >
          <p className="font-medium text-foreground">
            {v.brand} {v.model}
          </p>
          <p className="text-xs text-muted-foreground">
            {t(`color.${v.color}` as TranslationKey)} · {v.seats} seats
          </p>
        </button>
      </TableCell>

      <TableCell className="px-4 py-3 text-foreground">{v.year}</TableCell>

      <TableCell className="px-4 py-3 text-foreground">{v.mileage.toLocaleString()} km</TableCell>

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
            <DropdownMenuItem onClick={() => onViewDetails(v)}>
              <ExternalLink className="w-4 h-4 mr-2" />
              {t('vehicles.viewDetails')}
            </DropdownMenuItem>
            {canEdit && editHref && (
              <DropdownMenuItem asChild>
                <Link href={editHref}>
                  <Pencil className="w-4 h-4 mr-2" />
                  {t('common.edit')}
                </Link>
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}
