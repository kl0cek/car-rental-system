'use client';

import { useState, useCallback, useMemo } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  CheckCircle,
  XCircle,
  Loader2,
  Wrench,
  Clock,
} from 'lucide-react';
import { MiniCalendar } from './MiniCalendar';
import { useVehicleBookedDates } from '@/hooks/useVehicleBookedDates';
import type { Vehicle } from '@/types/vehicle';

interface AvailabilityCalendarProps {
  vehicle: Vehicle;
  dateFrom: string;
  dateTo: string;
  onDatesChange: (from: string, to: string) => void;
  available: boolean | null;
  availabilityLoading: boolean;
}

export function AvailabilityCalendar({
  vehicle,
  dateFrom,
  dateTo,
  onDatesChange,
  available,
  availabilityLoading,
}: AvailabilityCalendarProps) {
  const { bookedRanges } = useVehicleBookedDates(vehicle.id);

  const [calMonth, setCalMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [hoverDate, setHoverDate] = useState('');

  const today = useMemo(() => new Date().toISOString().slice(0, 10), []);

  const currentRentalEnd = useMemo(() => {
    if (vehicle.status !== 'rented') return null;
    const active = bookedRanges.find(([start, end]) => start <= today && end >= today);
    return active ? active[1] : null;
  }, [vehicle.status, bookedRanges, today]);

  const nextMonthVal = useMemo(
    () =>
      calMonth.month === 11
        ? { year: calMonth.year + 1, month: 0 }
        : { year: calMonth.year, month: calMonth.month + 1 },
    [calMonth]
  );

  const prevMonth = useCallback(
    () =>
      setCalMonth(({ year, month }) =>
        month === 0 ? { year: year - 1, month: 11 } : { year, month: month - 1 }
      ),
    []
  );

  const nextMonth = useCallback(
    () =>
      setCalMonth(({ year, month }) =>
        month === 11 ? { year: year + 1, month: 0 } : { year, month: month + 1 }
      ),
    []
  );

  const handleDayClick = useCallback(
    (dateStr: string) => {
      if (dateStr < today) return;
      if (!dateFrom || (dateFrom && dateTo)) {
        onDatesChange(dateStr, '');
      } else if (dateStr === dateFrom) {
        onDatesChange('', '');
      } else if (dateStr > dateFrom) {
        onDatesChange(dateFrom, dateStr);
        setHoverDate('');
      } else {
        onDatesChange(dateStr, '');
      }
    },
    [today, dateFrom, dateTo, onDatesChange]
  );

  const calendarHint = !dateFrom
    ? 'Kliknij dzień, aby wybrać datę rozpoczęcia'
    : !dateTo
      ? 'Teraz wybierz datę zakończenia'
      : null;

  const calendarProps = () => ({
    bookedRanges,
    selectedFrom: dateFrom,
    selectedTo: dateTo,
    hoverDate,
    onDayClick: handleDayClick,
    onDayHover: (d: string) => !dateTo && setHoverDate(d),
    onDayLeave: () => setHoverDate(''),
  });

  return (
    <div>
      {vehicle.status === 'maintenance' && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-400 text-xs font-medium">
          <Wrench className="w-3.5 h-3.5 shrink-0" />
          Pojazd jest w serwisie — data powrotu nie jest znana
        </div>
      )}

      {vehicle.status === 'rented' && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 text-yellow-700 dark:text-yellow-400 text-xs font-medium">
          <Clock className="w-3.5 h-3.5 shrink-0" />
          {currentRentalEnd
            ? `Aktualnie wynajęty — dostępny od ${currentRentalEnd}`
            : 'Aktualnie wynajęty — możliwa rezerwacja na późniejszy termin'}
        </div>
      )}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Kalendarz dostępności
        </h3>
        <div className="flex items-center gap-0.5">
          <button
            onClick={prevMonth}
            className="p-1 rounded hover:bg-secondary transition-colors"
            aria-label="Poprzedni miesiąc"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={nextMonth}
            className="p-1 rounded hover:bg-secondary transition-colors"
            aria-label="Następny miesiąc"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {calendarHint && <p className="text-xs text-primary font-medium mb-2">{calendarHint}</p>}

      <div className="flex items-center gap-4 text-[10px] text-muted-foreground mb-3 flex-wrap">
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-red-100 dark:bg-red-900/30 border border-red-300 dark:border-red-700" />
          Zarezerwowane
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm bg-primary/15 border border-primary/30" />
          Twój wybór
        </span>
      </div>

      <div className="flex gap-6 flex-wrap">
        <MiniCalendar year={calMonth.year} month={calMonth.month} {...calendarProps()} />
        <MiniCalendar year={nextMonthVal.year} month={nextMonthVal.month} {...calendarProps()} />
      </div>

      {(dateFrom || dateTo) && (
        <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium text-foreground">{dateFrom || '—'}</span>
          <span>→</span>
          <span className="font-medium text-foreground">{dateTo || '…'}</span>
          <button
            onClick={() => {
              onDatesChange('', '');
              setHoverDate('');
            }}
            className="ml-auto text-muted-foreground hover:text-foreground underline underline-offset-2 transition-colors"
          >
            Wyczyść
          </button>
        </div>
      )}

      {dateFrom && dateTo && (
        <div className="mt-2">
          {availabilityLoading ? (
            <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Sprawdzanie dostępności…
            </p>
          ) : available === true ? (
            <p className="flex items-center gap-1.5 text-xs text-green-600 dark:text-green-400 font-medium">
              <CheckCircle className="w-3.5 h-3.5" />
              Termin dostępny
            </p>
          ) : available === false ? (
            <p className="flex items-center gap-1.5 text-xs text-red-600 dark:text-red-400 font-medium">
              <XCircle className="w-3.5 h-3.5" />
              Termin niedostępny — pojazd jest już zarezerwowany w tym okresie
            </p>
          ) : null}
        </div>
      )}
    </div>
  );
}
