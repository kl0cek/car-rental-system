/**
 * In-memory mock store for vehicle reviews.
 *
 * Backend endpoints for reviews don't exist yet (planned to live in a NoSQL
 * store separate from the relational fleet/rental tables). Until then this
 * module imitates the API surface: it holds an in-memory list of reviews,
 * exposes CRUD/moderation operations that return API-shaped DTOs, and emits
 * a "changed" event so SWR hooks can revalidate after mutations.
 *
 * Everything here is `snake_case` to match the eventual REST contract — the
 * camelCase mapping happens in the hooks (same pattern as the rest of the
 * codebase).
 */

import type {
  ReviewApi,
  ReviewStatus,
  ReviewableRentalApi,
  PaginatedReviewsApi,
  ReviewSort,
  ModerationAction,
  ReviewAuthorApi,
} from '@/types/review';

type Listener = () => void;

const listeners = new Set<Listener>();

function emit(): void {
  for (const l of listeners) l();
}

export function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// ---------------------------------------------------------------------------
// Fixture data
// ---------------------------------------------------------------------------

const PLACEHOLDER_VEHICLE_IDS = [
  '11111111-1111-1111-1111-111111111111',
  '22222222-2222-2222-2222-222222222222',
  '33333333-3333-3333-3333-333333333333',
];

const FIXTURE_AUTHORS: ReviewAuthorApi[] = [
  {
    id: 'author-1',
    first_name: 'Anna',
    last_name: 'Nowak',
    avatar_url: null,
  },
  {
    id: 'author-2',
    first_name: 'Piotr',
    last_name: 'Kowalski',
    avatar_url: null,
  },
  {
    id: 'author-3',
    first_name: 'Marta',
    last_name: 'Wiśniewska',
    avatar_url: null,
  },
  {
    id: 'author-4',
    first_name: 'Tomasz',
    last_name: 'Lewandowski',
    avatar_url: null,
  },
];

let nextId = 1;
const reviews: ReviewApi[] = [];

function isoOffset(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString();
}

function seed(): void {
  const seedRows: Array<Partial<ReviewApi> & Pick<ReviewApi, 'vehicle_id' | 'rating' | 'body'>> = [
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[0],
      rating: 5,
      title: 'Świetne auto na weekendowy wyjazd',
      body: 'Wszystko zagrało — odbiór szybki, samochód czysty, prowadzi się rewelacyjnie. Polecam.',
      author: FIXTURE_AUTHORS[0],
      status: 'approved',
      created_at: isoOffset(2),
      helpful_count: 12,
      unhelpful_count: 1,
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[0],
      rating: 4,
      title: 'Bardzo dobry stosunek jakości do ceny',
      body: 'Drobny problem z aplikacją do otwierania, ale support pomógł w 5 minut. Sam pojazd super.',
      author: FIXTURE_AUTHORS[1],
      status: 'approved',
      created_at: isoOffset(5),
      helpful_count: 7,
      unhelpful_count: 0,
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[0],
      rating: 2,
      title: 'Brudne wnętrze',
      body: 'Auto sprawne, ale w środku okruchy po poprzednim kliencie. Liczyłem na lepszy standard.',
      author: FIXTURE_AUTHORS[2],
      status: 'approved',
      created_at: isoOffset(11),
      helpful_count: 3,
      unhelpful_count: 2,
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[1],
      rating: 5,
      title: null,
      body: 'Top, bez zastrzeżeń.',
      author: FIXTURE_AUTHORS[3],
      status: 'approved',
      created_at: isoOffset(1),
      helpful_count: 1,
      unhelpful_count: 0,
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[1],
      rating: 1,
      title: 'Coś dziwnego',
      body: 'Nie wiem co napisać.',
      author: FIXTURE_AUTHORS[0],
      status: 'pending',
      is_flagged: true,
      created_at: isoOffset(0),
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[2],
      rating: 4,
      title: 'Solidne SUV-y',
      body: 'Wynajmuję regularnie i zawsze wszystko gra. Tym razem opony na granicy, ale OK.',
      author: FIXTURE_AUTHORS[2],
      status: 'approved',
      created_at: isoOffset(20),
      helpful_count: 4,
      unhelpful_count: 0,
    },
    {
      vehicle_id: PLACEHOLDER_VEHICLE_IDS[2],
      rating: 3,
      title: 'Średnio',
      body: 'Spalanie wyższe niż w opisie. Reszta OK.',
      author: FIXTURE_AUTHORS[1],
      status: 'pending',
      created_at: isoOffset(0),
    },
  ];

  for (const row of seedRows) {
    reviews.push({
      id: `rev-${nextId++}`,
      vehicle_id: row.vehicle_id,
      rental_id: `rental-${nextId}`,
      author: row.author ?? FIXTURE_AUTHORS[0],
      rating: row.rating,
      title: row.title ?? null,
      body: row.body,
      status: row.status ?? 'approved',
      is_flagged: row.is_flagged ?? false,
      helpful_count: row.helpful_count ?? 0,
      unhelpful_count: row.unhelpful_count ?? 0,
      my_vote: null,
      created_at: row.created_at ?? new Date().toISOString(),
      updated_at: row.created_at ?? new Date().toISOString(),
      moderated_at: row.status === 'approved' ? (row.created_at ?? null) : null,
      moderated_by_id: row.status === 'approved' ? 'system' : null,
      rejection_reason: null,
    });
  }
}

seed();

// ---------------------------------------------------------------------------
// Reviewable rentals fixture
// ---------------------------------------------------------------------------

const reviewableRentals: ReviewableRentalApi[] = [
  {
    rental_id: 'mock-rental-a',
    reservation_id: 'mock-reservation-a',
    vehicle_id: PLACEHOLDER_VEHICLE_IDS[0],
    vehicle_brand: 'Toyota',
    vehicle_model: 'Corolla',
    vehicle_image_url: null,
    return_date: isoOffset(3),
    existing_review_id: null,
  },
  {
    rental_id: 'mock-rental-b',
    reservation_id: 'mock-reservation-b',
    vehicle_id: PLACEHOLDER_VEHICLE_IDS[1],
    vehicle_brand: 'BMW',
    vehicle_model: 'Seria 3',
    vehicle_image_url: null,
    return_date: isoOffset(14),
    existing_review_id: null,
  },
];

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

function sortReviews(arr: ReviewApi[], sort: ReviewSort): ReviewApi[] {
  const copy = [...arr];
  switch (sort) {
    case 'newest':
      copy.sort((a, b) => b.created_at.localeCompare(a.created_at));
      break;
    case 'top_rating':
      copy.sort((a, b) => b.rating - a.rating || b.created_at.localeCompare(a.created_at));
      break;
    case 'low_rating':
      copy.sort((a, b) => a.rating - b.rating || b.created_at.localeCompare(a.created_at));
      break;
    case 'most_helpful':
      copy.sort(
        (a, b) => b.helpful_count - a.helpful_count || b.created_at.localeCompare(a.created_at)
      );
      break;
  }
  return copy;
}

export interface VehicleReviewsQuery {
  vehicleId: string;
  sort: ReviewSort;
  offset: number;
  limit: number;
}

export function listVehicleReviews(q: VehicleReviewsQuery): PaginatedReviewsApi {
  const all = reviews.filter((r) => r.vehicle_id === q.vehicleId && r.status === 'approved');
  const sorted = sortReviews(all, q.sort);
  const slice = sorted.slice(q.offset, q.offset + q.limit);

  const breakdown: Record<1 | 2 | 3 | 4 | 5, number> = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  let sum = 0;
  for (const r of all) {
    breakdown[r.rating as 1 | 2 | 3 | 4 | 5] += 1;
    sum += r.rating;
  }

  return {
    items: slice,
    total: all.length,
    offset: q.offset,
    limit: q.limit,
    average_rating: all.length === 0 ? null : sum / all.length,
    rating_breakdown: breakdown,
  };
}

export interface ModerationQuery {
  status: ReviewStatus | 'flagged' | 'all';
  offset: number;
  limit: number;
}

export function listForModeration(q: ModerationQuery): PaginatedReviewsApi {
  let all: ReviewApi[];
  if (q.status === 'flagged') {
    all = reviews.filter((r) => r.is_flagged);
  } else if (q.status === 'all') {
    all = [...reviews];
  } else {
    all = reviews.filter((r) => r.status === q.status);
  }
  all.sort((a, b) => b.created_at.localeCompare(a.created_at));
  const slice = all.slice(q.offset, q.offset + q.limit);
  return {
    items: slice,
    total: all.length,
    offset: q.offset,
    limit: q.limit,
    average_rating: null,
    rating_breakdown: { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
  };
}

export function listReviewableRentals(): ReviewableRentalApi[] {
  return reviewableRentals.map((r) => ({
    ...r,
    existing_review_id: reviews.find((rev) => rev.rental_id === r.rental_id)?.id ?? null,
  }));
}

export function findReview(id: string): ReviewApi | undefined {
  return reviews.find((r) => r.id === id);
}

export function findReviewByRental(rentalId: string): ReviewApi | undefined {
  return reviews.find((r) => r.rental_id === rentalId);
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export interface CreateReviewInput {
  vehicle_id: string;
  rental_id: string;
  rating: number;
  title: string | null;
  body: string;
  author: ReviewAuthorApi;
}

export function createReview(input: CreateReviewInput): ReviewApi {
  const now = new Date().toISOString();
  const created: ReviewApi = {
    id: `rev-${nextId++}`,
    vehicle_id: input.vehicle_id,
    rental_id: input.rental_id,
    author: input.author,
    rating: input.rating,
    title: input.title,
    body: input.body,
    // New reviews always land in moderation queue — staff has to approve.
    status: 'pending',
    is_flagged: false,
    helpful_count: 0,
    unhelpful_count: 0,
    my_vote: null,
    created_at: now,
    updated_at: now,
    moderated_at: null,
    moderated_by_id: null,
    rejection_reason: null,
  };
  reviews.push(created);
  emit();
  return created;
}

export interface UpdateReviewInput {
  id: string;
  rating: number;
  title: string | null;
  body: string;
}

export function updateReview(input: UpdateReviewInput): ReviewApi {
  const target = reviews.find((r) => r.id === input.id);
  if (!target) throw new Error('Review not found');
  target.rating = input.rating;
  target.title = input.title;
  target.body = input.body;
  target.updated_at = new Date().toISOString();
  // Edits go back into the moderation queue (anti-bait-and-switch).
  target.status = 'pending';
  target.moderated_at = null;
  target.moderated_by_id = null;
  emit();
  return target;
}

export function deleteReview(id: string): void {
  const idx = reviews.findIndex((r) => r.id === id);
  if (idx >= 0) reviews.splice(idx, 1);
  emit();
}

export interface VoteInput {
  id: string;
  vote: 'helpful' | 'unhelpful' | null;
}

export function voteReview(input: VoteInput): ReviewApi {
  const target = reviews.find((r) => r.id === input.id);
  if (!target) throw new Error('Review not found');
  const prev = target.my_vote;
  if (prev === 'helpful') target.helpful_count = Math.max(0, target.helpful_count - 1);
  if (prev === 'unhelpful') target.unhelpful_count = Math.max(0, target.unhelpful_count - 1);
  if (input.vote === 'helpful') target.helpful_count += 1;
  if (input.vote === 'unhelpful') target.unhelpful_count += 1;
  target.my_vote = input.vote;
  emit();
  return target;
}

export interface ModerateInput {
  id: string;
  action: ModerationAction;
  reason?: string;
  moderatorId: string;
}

export function moderateReview(input: ModerateInput): ReviewApi | null {
  const target = reviews.find((r) => r.id === input.id);
  if (!target) throw new Error('Review not found');
  const now = new Date().toISOString();
  switch (input.action) {
    case 'approve':
      target.status = 'approved';
      target.moderated_at = now;
      target.moderated_by_id = input.moderatorId;
      target.is_flagged = false;
      target.rejection_reason = null;
      break;
    case 'reject':
      target.status = 'rejected';
      target.moderated_at = now;
      target.moderated_by_id = input.moderatorId;
      target.rejection_reason = input.reason ?? null;
      break;
    case 'flag':
      target.is_flagged = true;
      break;
    case 'unflag':
      target.is_flagged = false;
      break;
    case 'delete': {
      const idx = reviews.findIndex((r) => r.id === input.id);
      if (idx >= 0) reviews.splice(idx, 1);
      emit();
      return null;
    }
  }
  emit();
  return target;
}
