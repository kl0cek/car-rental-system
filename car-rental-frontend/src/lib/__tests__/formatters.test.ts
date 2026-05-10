import { formatDate, formatDateLong, getInitials } from '@/lib/formatters';

describe('formatDate', () => {
  it('formats ISO date in en-GB short month', () => {
    expect(formatDate('2026-05-03T12:00:00Z')).toMatch(/3 May 2026/);
  });
});

describe('formatDateLong', () => {
  it('formats ISO date with full month name', () => {
    expect(formatDateLong('2026-12-24T00:00:00Z')).toMatch(/(24 December 2026|23 December 2026)/);
  });
});

describe('getInitials', () => {
  it('returns first letters uppercased', () => {
    expect(getInitials('john', 'doe')).toBe('JD');
  });

  it('preserves diacritics correctly upper-cased', () => {
    expect(getInitials('łukasz', 'ąbcdef')).toBe('ŁĄ');
  });
});
