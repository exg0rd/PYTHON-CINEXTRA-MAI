from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date
import json
import ast


class MovieData(BaseModel):
    """Pydantic model for movie data validation"""
    title: str = Field(..., max_length=255, description="Movie title")
    description: Optional[str] = Field(None, description="Movie overview/description")
    year: Optional[int] = Field(None, ge=1900, le=2030, description="Release year")
    genre: Optional[str] = Field(None, max_length=100, description="Primary genre")
    director: Optional[str] = Field(None, max_length=255, description="Director name")
    rating: Optional[float] = Field(None, ge=0.0, le=10.0, description="Movie rating")
    duration: Optional[int] = Field(None, gt=0, description="Duration in minutes")
    release_date: Optional[date] = Field(None, description="Release date")
    poster_url: Optional[str] = Field(None, max_length=500, description="Poster image URL")
    imdb_id: Optional[str] = Field(None, description="IMDB ID")
    budget: Optional[int] = Field(None, ge=0, description="Movie budget")
    revenue: Optional[int] = Field(None, ge=0, description="Movie revenue")
    popularity: Optional[float] = Field(None, ge=0.0, description="Popularity score")
    vote_count: Optional[int] = Field(None, ge=0, description="Number of votes")

    @validator('year', pre=True)
    def validate_year(cls, v):
        if v is None or v == '':
            return None
        try:
            year = int(float(v))
            if 1900 <= year <= 2030:
                return year
            return None
        except (ValueError, TypeError):
            return None

    @validator('rating', pre=True)
    def validate_rating(cls, v):
        if v is None or v == '':
            return None
        try:
            rating = float(v)
            if 0.0 <= rating <= 10.0:
                return rating
            return None
        except (ValueError, TypeError):
            return None

    @validator('duration', pre=True)
    def validate_duration(cls, v):
        if v is None or v == '':
            return None
        try:
            duration = int(float(v))
            if duration > 0:
                return duration
            return None
        except (ValueError, TypeError):
            return None

    @validator('release_date', pre=True)
    def validate_release_date(cls, v):
        if v is None or v == '':
            return None
        try:
            if isinstance(v, str):
                # Handle different date formats
                from datetime import datetime
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                    try:
                        return datetime.strptime(v, fmt).date()
                    except ValueError:
                        continue
            return None
        except (ValueError, TypeError):
            return None

    @validator('poster_url', pre=True)
    def validate_poster_url(cls, v):
        if v is None or v == '':
            return None
        # If it's a relative path, convert to full URL
        if isinstance(v, str) and v.startswith('/'):
            return f"https://image.tmdb.org/t/p/w500{v}"
        return v

    class Config:
        str_strip_whitespace = True