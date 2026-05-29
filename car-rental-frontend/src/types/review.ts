// The backend stores reviews as immutable MongoDB documents. The supported
// surface is intentionally narrow: rating + free-text comment + author info.
// Concepts the previous mock had (helpful votes, moderation states, titles,
// edits) are NOT backed by an API — see CLAUDE.md / review_service.py.
export type ReviewSort = 'newest' | 'top_rating' | 'low_rating';

export interface ReviewAuthorApi {
  id: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
}

export interface ReviewApi {
  id: string;
  user_id: string;
  vehicle_id: string;
  rental_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
  author: ReviewAuthorApi;
}

export interface PaginatedReviewsApi {
  items: ReviewApi[];
  total: number;
  offset: number;
  limit: number;
}

export interface ReviewAuthor {
  id: string;
  firstName: string;
  lastName: string;
  avatarUrl: string | null;
}

export interface Review {
  id: string;
  userId: string;
  vehicleId: string;
  rentalId: string;
  rating: number;
  comment: string | null;
  createdAt: string;
  author: ReviewAuthor;
}

export interface PaginatedReviews {
  items: Review[];
  total: number;
  offset: number;
  limit: number;
}

export interface ReviewableRental {
  rentalId: string;
  vehicleId: string;
  vehicleBrand: string;
  vehicleModel: string;
  vehicleImageUrl: string | null;
  returnDate: string;
}

export interface CreateReviewPayload {
  rentalId: string;
  rating: number;
  comment: string | null;
}

function mapAuthor(api: ReviewAuthorApi): ReviewAuthor {
  return {
    id: api.id,
    firstName: api.first_name,
    lastName: api.last_name,
    avatarUrl: api.avatar_url,
  };
}

export function mapReview(api: ReviewApi): Review {
  return {
    id: api.id,
    userId: api.user_id,
    vehicleId: api.vehicle_id,
    rentalId: api.rental_id,
    rating: api.rating,
    comment: api.comment,
    createdAt: api.created_at,
    author: mapAuthor(api.author),
  };
}

export function mapPaginatedReviews(api: PaginatedReviewsApi): PaginatedReviews {
  return {
    items: api.items.map(mapReview),
    total: api.total,
    offset: api.offset,
    limit: api.limit,
  };
}
