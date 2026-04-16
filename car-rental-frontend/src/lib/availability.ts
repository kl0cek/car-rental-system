// This file contains mock functions to generate booked date ranges for vehicles and check if a specific date is booked.
export function getMockBookedRanges(vehicleId: string): Array<[string, string]> {
  const seed = vehicleId.charCodeAt(0) + vehicleId.charCodeAt(vehicleId.length - 1);
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth();
  const offsets: [number, number][] = [
    [(seed % 5) + 3, (seed % 5) + 6],
    [(seed % 7) + 11, (seed % 7) + 14],
    [(seed % 6) + 20, (seed % 6) + 23],
  ];
  return offsets.map(([s, e]) => [
    new Date(y, m, s).toISOString().slice(0, 10),
    new Date(y, m, e).toISOString().slice(0, 10),
  ]);
}

export function isDateBooked(dateStr: string, bookedRanges: Array<[string, string]>): boolean {
  return bookedRanges.some(([start, end]) => dateStr >= start && dateStr <= end);
}
