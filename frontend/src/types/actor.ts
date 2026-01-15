export interface Actor {
  person_id: number;
  name: string;
  profile_path?: string;
  movie_count: number;
  character?: string; // For cast roles
  order?: number; // For cast order
}

export interface MovieSummary {
  id: number;
  title: string;
  year?: number;
  genre?: string;
  rating?: number;
  poster_url?: string;
}

export interface CastRole {
  movie: MovieSummary;
  character?: string;
  order?: number;
}

export interface CrewRole {
  movie: MovieSummary;
  job?: string;
  department?: string;
}

export interface ActorDetail {
  person_id: number;
  name: string;
  profile_path?: string;
  cast_roles: CastRole[];
  crew_roles: CrewRole[];
}

export interface PaginatedActorsResponse {
  actors: Actor[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface CrewDepartment {
  [department: string]: Array<{
    person_id: number;
    name: string;
    job?: string;
    profile_path?: string;
    movie_count: number;
  }>;
}