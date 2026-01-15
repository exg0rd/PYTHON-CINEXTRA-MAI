export interface Subtitle {
  language: string;
  label: string;
  url: string;
}

export interface AudioTrack {
  language: string;
  label: string;
  default?: boolean;
}

export interface MovieSummary {
  id: number;
  title: string;
  year: number;
  genre: string;
  rating: number;
  poster_url?: string;
  average_user_rating?: number;
  review_count: number;
  // Video streaming fields
  video_file_id?: string;
  processing_status?: 'pending' | 'processing' | 'completed' | 'failed';
  available_qualities?: string[];
  hls_manifest_url?: string;
  duration_seconds?: number;
}

export interface MovieDetail extends MovieSummary {
  description: string;
  director: string;
  cast: string[];
  duration: number;
  release_date: string;
  // Additional video fields
  subtitles?: Subtitle[];
  audio_tracks?: AudioTrack[];
  imdb_id?: string;
  tmdb_id?: number;
}

export interface PaginatedMoviesResponse {
  movies: MovieSummary[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status_code: number;
}