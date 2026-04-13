import { Users, ShieldCheck, ExternalLink, MoreHorizontal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export interface Customer {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string | null;
  isVerified: boolean;
  createdAt: string;
  totalReservations: number;
}

interface CustomerTableProps {
  customers: Customer[];
  isLoading: boolean;
  search: string;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getInitials(first: string, last: string) {
  return `${first[0]}${last[0]}`.toUpperCase();
}

const COLS = ['Customer', 'Email', 'Phone', 'Reservations', 'Joined', 'Status', 'Actions'];

export function CustomerTable({ customers, isLoading, search }: CustomerTableProps) {
  if (isLoading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-14 w-full rounded-lg" />
        ))}
      </div>
    );
  }

  if (customers.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="w-14 h-14 rounded-full bg-secondary flex items-center justify-center mb-3">
          <Users className="w-7 h-7 text-muted-foreground" />
        </div>
        <p className="font-medium text-foreground">No customers found</p>
        {search && (
          <p className="text-sm text-muted-foreground mt-1">No results for &quot;{search}&quot;</p>
        )}
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {COLS.map((col) => (
            <TableHead
              key={col}
              className={`px-5 py-3 text-xs uppercase tracking-wider text-muted-foreground ${col === 'Actions' ? 'text-right' : ''}`}
            >
              {col}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {customers.map((c) => (
          <TableRow key={c.id}>
            <TableCell className="px-5 py-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0">
                  <span className="text-xs font-semibold text-secondary-foreground">
                    {getInitials(c.firstName, c.lastName)}
                  </span>
                </div>
                <p className="font-medium text-foreground">{c.firstName} {c.lastName}</p>
              </div>
            </TableCell>
            <TableCell className="px-5 py-4 text-sm text-muted-foreground">{c.email}</TableCell>
            <TableCell className="px-5 py-4 text-sm text-muted-foreground">
              {c.phone ?? <span className="text-muted-foreground/50">—</span>}
            </TableCell>
            <TableCell className="px-5 py-4 font-medium text-foreground">{c.totalReservations}</TableCell>
            <TableCell className="px-5 py-4 text-sm text-muted-foreground">{formatDate(c.createdAt)}</TableCell>
            <TableCell className="px-5 py-4">
              {c.isVerified ? (
                <Badge variant="secondary" className="gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  Verified
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">Unverified</Badge>
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
                    View profile
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
