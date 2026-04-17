'use client';

import { useReservations } from '@/hooks/useReservations';
import { useHiddenRows } from '@/hooks/useHiddenRows';
import { useCancelReservation } from '@/hooks/useCancelReservation';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { BookingRow } from './BookingRow';
import { BookingCard } from './BookingCard';

const COLS = ['Vehicle', 'Duration', 'Status', 'Total', 'Actions'];

function AllHiddenMessage({ onShowAll }: { onShowAll: () => void }) {
  return (
    <p className="py-6 text-sm text-center text-muted-foreground">
      All rows hidden.{' '}
      <button onClick={onShowAll} className="underline">
        Show all
      </button>
    </p>
  );
}

export default function BookingsList() {
  const { reservations, isLoading, mutate } = useReservations(5);
  const { hide, showAll, isHidden, hiddenCount } = useHiddenRows();
  const { cancel, loadingId } = useCancelReservation();

  const visible = reservations.filter((r) => !isHidden(r.id));

  const handleCancel = async (id: string) => {
    try {
      await cancel(id);
      await mutate();
    } catch {
      // ignore — could show a toast here
    }
  };

  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Bookings</CardTitle>
            <CardDescription className="mt-0.5">Your recent rental reservations</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {hiddenCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs text-muted-foreground"
                onClick={showAll}
              >
                Show {hiddenCount} hidden
              </Button>
            )}
            <Button variant="link" className="text-sm p-0 h-auto">
              View all
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full rounded-lg" />
            ))}
          </div>
        ) : reservations.length === 0 ? (
          <p className="p-6 text-sm text-muted-foreground text-center">No reservations yet.</p>
        ) : (
          <>
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    {COLS.map((col) => (
                      <TableHead
                        key={col}
                        className={`text-xs uppercase tracking-wider text-muted-foreground px-5 py-3 ${col === 'Actions' ? 'text-right' : ''}`}
                      >
                        {col}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visible.map((r) => (
                    <BookingRow
                      key={r.id}
                      reservation={r}
                      onHide={hide}
                      onCancel={handleCancel}
                      cancellingId={loadingId}
                    />
                  ))}
                  {visible.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} className="p-0">
                        <AllHiddenMessage onShowAll={showAll} />
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="md:hidden divide-y divide-border">
              {visible.map((r) => (
                <BookingCard
                  key={r.id}
                  reservation={r}
                  onHide={hide}
                  onCancel={handleCancel}
                  cancellingId={loadingId}
                />
              ))}
              {visible.length === 0 && <AllHiddenMessage onShowAll={showAll} />}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
