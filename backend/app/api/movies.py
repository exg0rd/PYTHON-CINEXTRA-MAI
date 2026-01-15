from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime
import math

from ..db.database import get_db
from ..db.models import Movie, Review
from ..core.search import MovieSearchEngine, SearchResult, SortCriteria, SortOrder, SearchResult
from ..core.analytics import activity_logger
from .models import MovieSummary, MovieDetail, PaginatedMovies, SearchParams, HealthResponse
from .exceptions import MovieNotFoundError, InvalidPaginationError, DatabaseConnectionError
from .auth import get_current_user_optional

router = APIRouter(prefix="/api", tags=["movies"])


def get_movie_review_stats(db: Session, movie_id: int):
    """Get review statistics for a movie"""
    stats = (
        db.query(
            func.avg(Review.rating).label('average_rating'),
            func.count(Review.id).label('review_count')
        )
        .filter(Review.movie_id == movie_id)
        .first()
    )
    
    return {
        'average_user_rating': float(stats.average_rating) if stats.average_rating else None,
        'review_count': int(stats.review_count) if stats.review_count else 0
    }


def get_movies_with_review_stats(db: Session, movies):
    """Add review statistics to a list of movies"""
    movie_summaries = []
    
    for movie in movies:
        stats = get_movie_review_stats(db, movie.id)
        
        movie_summary = MovieSummary(
            id=movie.id,
            title=movie.title,
            year=movie.year,
            genre=movie.genre,
            rating=movie.rating,
            poster_url=movie.poster_url,
            average_user_rating=stats['average_user_rating'],
            review_count=stats['review_count']
        )
        movie_summaries.append(movie_summary)
    
    return movie_summaries


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(func.count(Movie.id)).scalar()
        db_status = "connected"
    except SQLAlchemyError as e:
        db_status = "disconnected"
    except Exception as e:
        db_status = "error"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "unhealthy",
        timestamp=datetime.utcnow(),
        database=db_status
    )


@router.get("/movies", response_model=PaginatedMovies)
async def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[SortCriteria] = Query(None, description="Sort criteria"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    db: Session = Depends(get_db)
):
    """Get paginated list of movies with optional sorting"""
    try:
        # Validate pagination parameters
        if page < 1:
            raise InvalidPaginationError("Page number must be greater than 0", "page")
        if per_page < 1 or per_page > 100:
            raise InvalidPaginationError("Items per page must be between 1 and 100", "per_page")
        
        # Use search engine for consistent sorting and pagination
        search_engine = MovieSearchEngine(db)
        result = search_engine.search_movies(
            query=None,  # No search query, just listing
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=per_page
        )
        
        # Convert to MovieSummary objects
        movie_summaries = []
        for movie_dict in result.movies:
            movie_summary = MovieSummary(
                id=movie_dict['id'],
                title=movie_dict['title'],
                year=movie_dict['year'],
                genre=movie_dict['genre'],
                rating=movie_dict['rating'],
                poster_url=movie_dict['poster_url'],
                average_user_rating=movie_dict['average_user_rating'],
                review_count=movie_dict['review_count']
            )
            movie_summaries.append(movie_summary)
        
        return PaginatedMovies(
            movies=movie_summaries,
            total=result.total_count,
            page=result.current_page,
            per_page=per_page,
            total_pages=result.total_pages,
            has_next=result.current_page < result.total_pages,
            has_prev=result.current_page > 1
        )
    
    except InvalidPaginationError:
        raise
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/movies/search", response_model=PaginatedMovies)
async def search_movies(
    q: str = Query(..., description="Search query"),
    sort_by: Optional[SortCriteria] = Query(None, description="Sort criteria"),
    sort_order: SortOrder = Query(SortOrder.DESC, description="Sort order"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Search movies with optional sorting"""
    try:
        # Validate pagination parameters
        if page < 1:
            raise InvalidPaginationError("Page number must be greater than 0", "page")
        if per_page < 1 or per_page > 100:
            raise InvalidPaginationError("Items per page must be between 1 and 100", "per_page")
        
        # Validate search query
        if not q or len(q.strip()) == 0:
            raise HTTPException(status_code=422, detail="Search query cannot be empty")
        
        # Use search engine
        search_engine = MovieSearchEngine(db)
        result = search_engine.search_movies(
            query=q.strip(),
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=per_page
        )
        
        # Log search analytics
        await activity_logger.log_search_query(
            query=q.strip(),
            results_count=result.total_count,
            user_id=current_user.id if current_user else None,
            filters={
                "sort_by": sort_by.value if sort_by else None,
                "sort_order": sort_order.value,
                "page": page
            }
        )
        
        # Convert to MovieSummary objects
        movie_summaries = []
        for movie_dict in result.movies:
            movie_summary = MovieSummary(
                id=movie_dict['id'],
                title=movie_dict['title'],
                year=movie_dict['year'],
                genre=movie_dict['genre'],
                rating=movie_dict['rating'],
                poster_url=movie_dict['poster_url'],
                average_user_rating=movie_dict['average_user_rating'],
                review_count=movie_dict['review_count']
            )
            movie_summaries.append(movie_summary)
        
        return PaginatedMovies(
            movies=movie_summaries,
            total=result.total_count,
            page=result.current_page,
            per_page=per_page,
            total_pages=result.total_pages,
            has_next=result.current_page < result.total_pages,
            has_prev=result.current_page > 1
        )
    
    except InvalidPaginationError:
        raise
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/movies/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    db: Session = Depends(get_db)
):
    """Get search suggestions for autocomplete"""
    try:
        if len(q.strip()) < 2:
            raise HTTPException(status_code=422, detail="Query must be at least 2 characters long")
        
        search_engine = MovieSearchEngine(db)
        suggestions = search_engine.get_search_suggestions(q.strip())
        
        return {"suggestions": suggestions}
    
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/movies/{movie_id}", response_model=MovieDetail)
async def get_movie_detail(
    movie_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """Get detailed information for a specific movie"""
    try:
        # Validate movie_id
        if movie_id < 1:
            raise HTTPException(status_code=422, detail="Movie ID must be a positive integer")
        
        # Load movie with cast and crew relationships
        movie = (
            db.query(Movie)
            .options(joinedload(Movie.cast), joinedload(Movie.crew))
            .filter(Movie.id == movie_id)
            .first()
        )
        
        if not movie:
            raise MovieNotFoundError(movie_id)
        
        # Log movie view
        await activity_logger.log_movie_view(
            movie_id=movie_id,
            user_id=current_user.id if current_user else None
        )
        
        # Get review statistics
        stats = get_movie_review_stats(db, movie_id)
        
        # Get cast information (top 10 cast members)
        cast_list = []
        for cast_member in sorted(movie.cast, key=lambda x: x.order or 999)[:10]:
            cast_list.append(cast_member.name)
        
        # Get director from crew
        director = "Unknown"
        for crew_member in movie.crew:
            if crew_member.job == "Director":
                director = crew_member.name
                break
        
        # Create movie detail response with review statistics
        movie_detail = MovieDetail(
            id=movie.id,
            title=movie.title,
            description=movie.description,
            year=movie.year,
            genre=movie.genre,
            director=director,
            rating=movie.rating,
            duration=movie.duration,
            release_date=movie.release_date,
            poster_url=movie.poster_url,
            imdb_id=movie.imdb_id,
            budget=movie.budget,
            revenue=movie.revenue,
            popularity=movie.popularity,
            vote_count=movie.vote_count,
            created_at=movie.created_at,
            updated_at=movie.updated_at,
            average_user_rating=stats['average_user_rating'],
            review_count=stats['review_count'],
            cast=cast_list,
            # Video fields
            video_file_id=movie.video_file_id,
            processing_status=movie.processing_status,
            hls_manifest_url=movie.hls_manifest_url,
            available_qualities=movie.available_qualities or [],
            duration_seconds=movie.duration_seconds,
            subtitles=[],  # TODO: Add subtitle support
            audio_tracks=[]  # TODO: Add audio track support
        )
        
        return movie_detail
    
    except MovieNotFoundError:
        raise
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")