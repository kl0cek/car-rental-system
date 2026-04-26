'use client';

import { ShieldCheck, ExternalLink, MoreHorizontal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { TableCell, TableRow } from '@/components/ui/table';
import { formatDate, getInitials } from '@/lib/formatters';
import type { Customer } from '@/types/customer';
import { useTranslation } from '@/i18n/useTranslation';

export function CustomerRow({ customer: c }: { customer: Customer }) {
  const { t } = useTranslation();
  return (
    <TableRow>
      <TableCell className="px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0 overflow-hidden">
            {c.avatarUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={c.avatarUrl}
                alt={getInitials(c.firstName, c.lastName)}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-xs font-semibold text-secondary-foreground">
                {getInitials(c.firstName, c.lastName)}
              </span>
            )}
          </div>
          <p className="font-medium text-foreground">
            {c.firstName} {c.lastName}
          </p>
        </div>
      </TableCell>
      <TableCell className="px-5 py-4 text-sm text-muted-foreground">{c.email}</TableCell>
      <TableCell className="px-5 py-4 text-sm text-muted-foreground">
        {c.phone ?? <span className="text-muted-foreground/50">—</span>}
      </TableCell>
      <TableCell className="px-5 py-4 font-medium text-muted-foreground/50">—</TableCell>
      <TableCell className="px-5 py-4 text-sm text-muted-foreground">
        {formatDate(c.createdAt)}
      </TableCell>
      <TableCell className="px-5 py-4">
        {c.isVerified ? (
          <Badge variant="secondary" className="gap-1">
            <ShieldCheck className="w-3 h-3" />
            {t('account.verified')}
          </Badge>
        ) : (
          <Badge variant="outline" className="text-muted-foreground">
            {t('account.notVerified')}
          </Badge>
        )}
      </TableCell>
      <TableCell className="px-5 py-4 text-right">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem disabled>
              <ExternalLink className="w-4 h-4 mr-2" />
              {t('customers.viewProfile')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </TableCell>
    </TableRow>
  );
}
