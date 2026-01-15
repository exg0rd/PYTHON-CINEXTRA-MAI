from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class ReviewCreate(BaseModel):
    """Request model for creating a review"""
    rating: int = Field(..., ge=1, le=10, description="Rating from 1 to 10")
    review_text: Optional[str] = Field(None, max_length=2000, description="Review text content")

    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class ReviewUpdate(BaseModel):
    """Request model for updating a review"""
    rating: Optional[int] = Field(None, ge=1, le=10, description="Rating from 1 to 10")
    review_text: Optional[str] = Field(None, max_length=2000, description="Review text content")

    @validator('review_text')
    def validate_review_text(cls, v):
        if v is not None and len(v.strip()) == 0:
            return None
        return v


class UserSummary(BaseModel):
    """Summary user information for reviews"""
    id: int
    username: str

    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Response model for review information"""
    id: int
    user_id: int
    movie_id: int
    rating: int
    review_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    user: UserSummary

    class Config:
        from_attributes = True


class PaginatedReviews(BaseModel):
    """Response model for paginated review lists"""
    reviews: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class MovieSummary(BaseModel):
    """Response model for movie list items"""
    id: int
    title: str
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    poster_url: Optional[str] = None
    average_user_rating: Optional[float] = None
    review_count: int = 0

    class Config:
        from_attributes = True


class MovieDetail(BaseModel):
    """Response model for detailed movie information"""
    id: int
    title: str
    description: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    director: Optional[str] = None
    rating: Optional[float] = None
    duration: Optional[int] = None
    release_date: Optional[date] = None
    poster_url: Optional[str] = None
    imdb_id: Optional[str] = None
    budget: Optional[int] = None
    revenue: Optional[int] = None
    popularity: Optional[float] = None
    vote_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    average_user_rating: Optional[float] = None
    review_count: int = 0
    cast: List[str] = []  # List of main cast member names
    
    # Video fields
    video_file_id: Optional[str] = None
    processing_status: Optional[str] = None
    hls_manifest_url: Optional[str] = None
    available_qualities: List[str] = []
    duration_seconds: Optional[int] = None
    subtitles: List[dict] = []
    audio_tracks: List[dict] = []

    class Config:
        from_attributes = True


class PaginatedMovies(BaseModel):
    """Response model for paginated movie lists"""
    movies: List[MovieSummary]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool


class SearchParams(BaseModel):
    """Query parameters for movie search"""
    q: Optional[str] = Field(None, description="Search query")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Filter by year")
    genre: Optional[str] = Field(None, description="Filter by genre")
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    timestamp: datetime
    database: str


class ActorResponse(BaseModel):
    """Response model for actor data"""
    person_id: int
    name: str
    profile_path: Optional[str] = None
    movie_count: int
    character: Optional[str] = None  # For cast roles
    order: Optional[int] = None  # For cast order

    class Config:
        from_attributes = True


class MovieSummaryResponse(BaseModel):
    """Response model for movie summary data in actor details"""
    id: int
    title: str
    year: Optional[int] = None
    genre: Optional[str] = None
    rating: Optional[float] = None
    poster_url: Optional[str] = None

    class Config:
        from_attributes = True


class ActorDetailResponse(BaseModel):
    """Response model for detailed actor information"""
    person_id: int
    name: str
    profile_path: Optional[str] = None
    cast_roles: List[Dict[str, Any]]
    crew_roles: List[Dict[str, Any]]

    class Config:
        from_attributes = True


class PaginatedActorsResponse(BaseModel):
    """Response model for paginated actor lists"""
    actors: List[ActorResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool