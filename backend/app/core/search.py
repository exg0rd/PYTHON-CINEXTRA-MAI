"""
Movie search engine with sorting capabilities
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc
from app.db.models import Movie, Review, Cast, Crew
from pydantic import BaseModel


class SortCriteria(str, Enum):
    YEAR = "year"
    RATING = "rating"
    REVIEW_COUNT = "review_count"
    RELEVANCE = "relevance"
    TITLE = "title"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SearchResult(BaseModel):
    movies: List[Dict[str, Any]]
    total_count: int
    current_page: int
    total_pages: int
    query: Optional[str] = None
    sort_by: Optional[SortCriteria] = None
    sort_order: SortOrder = SortOrder.DESC
    search_time_ms: float = 0.0


class MovieSearchEngine:
    def __init__(self, db_session: Session):
        self.db = db_session

    def search_movies(
        self,
        query: Optional[str] = None,
        sort_by: Optional[SortCriteria] = None,
        sort_order: SortOrder = SortOrder.DESC,
        page: int = 1,
        limit: int = 20,
        include_actor_search: bool = True
    ) -> SearchResult:
        """
        Search movies with optional sorting and pagination
        """
        import time
        start_time = time.time()
        
        # Start with base query
        base_query = self.db.query(Movie)
        
        # Apply search filter if query provided
        if query and query.strip():
            search_term = f"%{query.strip()}%"
            
            # Base movie search conditions
            movie_conditions = [
                Movie.title.ilike(search_term),
                Movie.description.ilike(search_term),
                Movie.genre.ilike(search_term),
                Movie.director.ilike(search_term)
            ]
            
            # Add actor search if enabled
            if include_actor_search:
                # Find movies by cast
                cast_movie_ids = self.db.query(Cast.movie_id).filter(
                    Cast.name.ilike(search_term)
                ).distinct().subquery()
                
                # Find movies by crew
                crew_movie_ids = self.db.query(Crew.movie_id).filter(
                    Crew.name.ilike(search_term)
                ).distinct().subquery()
                
                # Add actor search conditions
                movie_conditions.extend([
                    Movie.id.in_(self.db.query(cast_movie_ids.c.movie_id)),
                    Movie.id.in_(self.db.query(crew_movie_ids.c.movie_id))
                ])
            
            base_query = base_query.filter(or_(*movie_conditions))
        
        # Apply sorting
        if sort_by:
            base_query = self._apply_sort(base_query, sort_by, sort_order)
        else:
            # Default sort by ID for consistent pagination
            base_query = base_query.order_by(Movie.id)
        
        # Get total count before pagination
        total_count = base_query.count()
        
        # Apply pagination
        offset = (page - 1) * limit
        movies_query = base_query.offset(offset).limit(limit)
        
        # Execute query and convert to dict
        movies = []
        for movie in movies_query.all():
            # Get review stats for this movie
            review_stats = self.db.query(
                func.count(Review.id).label('review_count'),
                func.avg(Review.rating).label('avg_rating')
            ).filter(Review.movie_id == movie.id).first()
            
            movie_dict = {
                'id': movie.id,
                'title': movie.title,
                'description': movie.description,
                'year': movie.year,
                'genre': movie.genre,
                'director': movie.director,
                'rating': movie.rating,
                'duration': movie.duration,
                'release_date': movie.release_date.isoformat() if movie.release_date else None,
                'poster_url': movie.poster_url,
                'review_count': review_stats.review_count or 0,
                'average_user_rating': float(review_stats.avg_rating) if review_stats.avg_rating else None
            }
            movies.append(movie_dict)
        
        # Calculate pagination info
        total_pages = (total_count + limit - 1) // limit
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        return SearchResult(
            movies=movies,
            total_count=total_count,
            current_page=page,
            total_pages=total_pages,
            query=query,
            sort_by=sort_by,
            sort_order=sort_order,
            search_time_ms=search_time
        )

    def _apply_sort(self, query, sort_by: SortCriteria, sort_order: SortOrder):
        """Apply sorting to the query"""
        if sort_by == SortCriteria.YEAR:
            if sort_order == SortOrder.DESC:
                return query.order_by(desc(Movie.year))
            else:
                return query.order_by(asc(Movie.year))
                
        elif sort_by == SortCriteria.RATING:
            # Sort by movie rating (we'll enhance this later to include user ratings)
            if sort_order == SortOrder.DESC:
                return query.order_by(desc(Movie.rating))
            else:
                return query.order_by(asc(Movie.rating))
                
        elif sort_by == SortCriteria.TITLE:
            if sort_order == SortOrder.DESC:
                return query.order_by(desc(Movie.title))
            else:
                return query.order_by(asc(Movie.title))
                
        elif sort_by == SortCriteria.REVIEW_COUNT:
            # Join with reviews and sort by count
            query = query.outerjoin(Review, Movie.id == Review.movie_id)
            query = query.group_by(Movie.id)
            if sort_order == SortOrder.DESC:
                return query.order_by(desc(func.count(Review.id)))
            else:
                return query.order_by(asc(func.count(Review.id)))
        
        # Default fallback
        return query.order_by(Movie.id)

    def get_search_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Get search suggestions for autocomplete"""
        if not partial_query or len(partial_query) < 2:
            return []
        
        search_term = f"%{partial_query}%"
        
        # Get movie titles that match
        titles = self.db.query(Movie.title).filter(
            Movie.title.ilike(search_term)
        ).limit(limit).all()
        
        return [title[0] for title in titles]