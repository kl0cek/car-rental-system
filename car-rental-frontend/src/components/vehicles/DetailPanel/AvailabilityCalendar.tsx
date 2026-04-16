'use client';

import { useState, useCallback, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Info } from 'lucide-react';
import { MiniCalendar } from './MiniCalendar';
import { getMockBookedRanges } from '@/lib/availability';
import type { Vehicle } from '@/types/vehicle';

interface AvailabilityCalendarProps {
  vehicle: Vehicle;
  dateFrom: string;
  dateTo: string;
  onDatesChange: (from: string, to: string) => void;
}

export function AvailabilityCalendar({
  vehicle,
  dateFrom,
  dateTo,
  onDatesChange,
}: AvailabilityCalendarProps) {
  const [calMonth, setCalMonth] = useState(() => {
    const now = new Date();
    return { year: now.getFullYear(), month: now.getMonth() };
  });
  const [hoverDate, setHoverDate] = useState('');

  // MOCK: zastąpić danymi z GET /api/vehicles/{id}/availability gdy endpoint gotowy
  const bookedRanges = useMemo(() => getMockBookedRanges(vehicle.id), [vehicle.id]);

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
    [dateFrom, dateTo, onDatesChange]
  );

  const calendarHint = !dateFrom
    ? 'Kliknij dzień, aby wybrać datę rozpoczęcia'
    : !dateTo
      ? 'Teraz wybierz datę zakończenia'
      : null;

  const calendarProps = useMemo(
    () => ({
      bookedRanges,
      selectedFrom: dateFrom,
      selectedTo: dateTo,
      hoverDate,
      onDayClick: handleDayClick,
      onDayHover: (d: string) => !dateTo && setHoverDate(d),
      onDayLeave: () => setHoverDate(''),
    }),
    [bookedRanges, dateFrom, dateTo, hoverDate, handleDayClick]
  );

  return (
    <div>
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
        <span className="flex items-center gap-1.5 opacity-60">
          <Info className="w-3 h-3" />
          {/* TODO: dane mock – zastąpić GET /api/vehicles/{id}/availability */}
          Dane przykładowe
        </span>
      </div>

      <div className="flex gap-6 flex-wrap">
        <MiniCalendar year={calMonth.year} month={calMonth.month} {...calendarProps} />
        <MiniCalendar year={nextMonthVal.year} month={nextMonthVal.month} {...calendarProps} />
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
    </div>
  );
}
