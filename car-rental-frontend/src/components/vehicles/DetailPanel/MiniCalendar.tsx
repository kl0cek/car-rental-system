'use client';

import { isDateBooked } from '@/lib/availability';

interface MiniCalendarProps {
  year: number;
  month: number;
  bookedRanges: Array<[string, string]>;
  selectedFrom: string;
  selectedTo: string;
  hoverDate: string;
  onDayClick: (date: string) => void;
  onDayHover: (date: string) => void;
  onDayLeave: () => void;
}

export function MiniCalendar({
  year,
  month,
  bookedRanges,
  selectedFrom,
  selectedTo,
  hoverDate,
  onDayClick,
  onDayHover,
  onDayLeave,
}: MiniCalendarProps) {
  const today = new Date().toISOString().slice(0, 10);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();
  const startOffset = (firstDayOfWeek + 6) % 7; // Monday-first
  const monthName = new Date(year, month, 1).toLocaleString('default', {
    month: 'long',
    year: 'numeric',
  });

  const effectiveTo = selectedTo || (selectedFrom && hoverDate > selectedFrom ? hoverDate : '');
  const isPreview = !selectedTo && !!effectiveTo;

  const cells: (number | null)[] = [];
  for (let i = 0; i < startOffset; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div className="flex-1 min-w-65">
      <p className="text-xs font-semibold text-center text-foreground mb-2">{monthName}</p>
      <div className="grid grid-cols-7 gap-0.5 text-center">
        {['Pn', 'Wt', 'Śr', 'Cz', 'Pt', 'Sb', 'Nd'].map((d, i) => (
          <div key={i} className="text-[10px] text-muted-foreground font-medium py-0.5">
            {d}
          </div>
        ))}
        {cells.map((day, i) => {
          if (day === null) return <div key={`e-${i}`} />;

          const dateStr = new Date(year, month, day).toISOString().slice(0, 10);
          const isPast = dateStr < today;
          const booked = isDateBooked(dateStr, bookedRanges);
          const isClickable = !isPast && !booked;
          const isToday = dateStr === today;
          const isStart = dateStr === selectedFrom;
          const isEnd = dateStr === selectedTo;
          const inConfirmedRange =
            selectedFrom && selectedTo && dateStr > selectedFrom && dateStr < selectedTo;
          const inPreviewRange =
            isPreview &&
            selectedFrom &&
            effectiveTo &&
            dateStr > selectedFrom &&
            dateStr < effectiveTo;
          const isHoverEnd = isPreview && dateStr === effectiveTo;

          let cls = 'text-[11px] rounded py-1 leading-tight transition-colors select-none ';

          if (isPast) {
            cls += 'text-muted-foreground/30 cursor-not-allowed';
          } else if (booked) {
            cls +=
              'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 font-medium cursor-not-allowed';
          } else if (isStart) {
            cls += 'bg-primary text-primary-foreground font-bold cursor-pointer rounded-l-full';
          } else if (isEnd) {
            cls += 'bg-primary text-primary-foreground font-bold cursor-pointer rounded-r-full';
          } else if (isHoverEnd) {
            cls += 'bg-primary/50 text-primary-foreground font-semibold cursor-pointer';
          } else if (inConfirmedRange) {
            cls += 'bg-primary/15 text-foreground cursor-pointer';
          } else if (inPreviewRange) {
            cls += 'bg-primary/[0.08] text-foreground cursor-pointer';
          } else if (isToday) {
            cls +=
              'ring-1 ring-primary text-primary font-semibold cursor-pointer hover:bg-secondary';
          } else {
            cls += 'text-foreground cursor-pointer hover:bg-secondary';
          }

          return (
            <button
              key={day}
              type="button"
              className={cls}
              disabled={!isClickable}
              onClick={() => onDayClick(dateStr)}
              onMouseEnter={() => isClickable && onDayHover(dateStr)}
              onMouseLeave={onDayLeave}
              aria-label={booked ? `${dateStr} – zarezerwowane` : dateStr}
            >
              {day}
            </button>
          );
        })}
      </div>
    </div>
  );
}
