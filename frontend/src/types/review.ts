export interface UserSummary {
  id: number;
  username: string;
}

export interface Review {
  id: number;
  user_id: number;
  movie_id: number;
  rating: number;
  review_text?: string;
  created_at: string;
  updated_at: string;
  user: UserSummary;
}

export interface ReviewCreate {
  rating: number;
  review_text?: string;
}

export interface ReviewUpdate {
  rating?: number;
  review_text?: string;
}

export interface PaginatedReviewsResponse {
  reviews: Review[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}