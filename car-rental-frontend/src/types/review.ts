export type ReviewStatus = 'pending' | 'approved' | 'rejected';
export type ReviewSort = 'newest' | 'top_rating' | 'low_rating' | 'most_helpful';

export interface ReviewAuthorApi {
  id: string;
  first_name: string;
  last_name: string;
  avatar_url: string | null;
}

export interface ReviewApi {
  id: string;
  vehicle_id: string;
  rental_id: string;
  author: ReviewAuthorApi;
  rating: number;
  title: string | null;
  body: string;
  status: ReviewStatus;
  is_flagged: boolean;
  helpful_count: number;
  unhelpful_count: number;
  my_vote: 'helpful' | 'unhelpful' | null;
  created_at: string;
  updated_at: string;
  moderated_at: string | null;
  moderated_by_id: string | null;
  rejection_reason: string | null;
}

export interface PaginatedReviewsApi {
  items: ReviewApi[];
  total: number;
  offset: number;
  limit: number;
  average_rating: number | null;
  rating_breakdown: Record<1 | 2 | 3 | 4 | 5, number>;
}

export interface ReviewAuthor {
  id: string;
  firstName: string;
  lastName: string;
  avatarUrl: string | null;
}

export interface Review {
  id: string;
  vehicleId: string;
  rentalId: string;
  author: ReviewAuthor;
  rating: number;
  title: string | null;
  body: string;
  status: ReviewStatus;
  isFlagged: boolean;
  helpfulCount: number;
  unhelpfulCount: number;
  myVote: 'helpful' | 'unhelpful' | null;
  createdAt: string;
  updatedAt: string;
  moderatedAt: string | null;
  moderatedById: string | null;
  rejectionReason: string | null;
}

export interface PaginatedReviews {
  items: Review[];
  total: number;
  offset: number;
  limit: number;
  averageRating: number | null;
  ratingBreakdown: Record<1 | 2 | 3 | 4 | 5, number>;
}

export interface ReviewableRentalApi {
  rental_id: string;
  reservation_id: string;
  vehicle_id: string;
  vehicle_brand: string;
  vehicle_model: string;
  vehicle_image_url: string | null;
  return_date: string;
  existing_review_id: string | null;
}

export interface ReviewableRental {
  rentalId: string;
  reservationId: string;
  vehicleId: string;
  vehicleBrand: string;
  vehicleModel: string;
  vehicleImageUrl: string | null;
  returnDate: string;
  existingReviewId: string | null;
}

export interface CreateReviewPayload {
  vehicleId: string;
  rentalId: string;
  rating: number;
  title: string | null;
  body: string;
}

export interface UpdateReviewPayload {
  rating: number;
  title: string | null;
  body: string;
}

export type ModerationAction = 'approve' | 'reject' | 'flag' | 'unflag' | 'delete';

export interface ModerateReviewPayload {
  action: ModerationAction;
  reason?: string;
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
    vehicleId: api.vehicle_id,
    rentalId: api.rental_id,
    author: mapAuthor(api.author),
    rating: api.rating,
    title: api.title,
    body: api.body,
    status: api.status,
    isFlagged: api.is_flagged,
    helpfulCount: api.helpful_count,
    unhelpfulCount: api.unhelpful_count,
    myVote: api.my_vote,
    createdAt: api.created_at,
    updatedAt: api.updated_at,
    moderatedAt: api.moderated_at,
    moderatedById: api.moderated_by_id,
    rejectionReason: api.rejection_reason,
  };
}

export function mapPaginatedReviews(api: PaginatedReviewsApi): PaginatedReviews {
  return {
    items: api.items.map(mapReview),
    total: api.total,
    offset: api.offset,
    limit: api.limit,
    averageRating: api.average_rating,
    ratingBreakdown: api.rating_breakdown,
  };
}

export function mapReviewableRental(api: ReviewableRentalApi): ReviewableRental {
  return {
    rentalId: api.rental_id,
    reservationId: api.reservation_id,
    vehicleId: api.vehicle_id,
    vehicleBrand: api.vehicle_brand,
    vehicleModel: api.vehicle_model,
    vehicleImageUrl: api.vehicle_image_url,
    returnDate: api.return_date,
    existingReviewId: api.existing_review_id,
  };
}
