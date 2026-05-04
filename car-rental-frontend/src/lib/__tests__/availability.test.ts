import { getMockBookedRanges, isDateBooked } from '@/lib/availability';

describe('isDateBooked', () => {
  const ranges: Array<[string, string]> = [
    ['2026-05-10', '2026-05-15'],
    ['2026-06-01', '2026-06-03'],
  ];

  it('returns true for date in range (inclusive start)', () => {
    expect(isDateBooked('2026-05-10', ranges)).toBe(true);
  });

  it('returns true for date in range (inclusive end)', () => {
    expect(isDateBooked('2026-05-15', ranges)).toBe(true);
  });

  it('returns true for date in middle of range', () => {
    expect(isDateBooked('2026-05-12', ranges)).toBe(true);
  });

  it('returns false for date before all ranges', () => {
    expect(isDateBooked('2026-05-09', ranges)).toBe(false);
  });

  it('returns false for date between ranges', () => {
    expect(isDateBooked('2026-05-20', ranges)).toBe(false);
  });

  it('returns false when ranges empty', () => {
    expect(isDateBooked('2026-05-10', [])).toBe(false);
  });
});

describe('getMockBookedRanges', () => {
  it('returns 3 ranges', () => {
    expect(getMockBookedRanges('vehicle-abc')).toHaveLength(3);
  });

  it('is deterministic for same vehicleId', () => {
    expect(getMockBookedRanges('foo')).toEqual(getMockBookedRanges('foo'));
  });

  it('produces YYYY-MM-DD formatted dates', () => {
    const ranges = getMockBookedRanges('test-vehicle');
    for (const [start, end] of ranges) {
      expect(start).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(end).toMatch(/^\d{4}-\d{2}-\d{2}$/);
      expect(start <= end).toBe(true);
    }
  });
});
