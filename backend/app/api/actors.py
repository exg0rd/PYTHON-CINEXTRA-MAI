from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, desc
from typing import List, Optional
import math

from ..db.database import get_db
from ..db.models import Cast, Movie, Crew
from .models import ActorResponse, ActorDetailResponse, PaginatedActorsResponse, MovieSummaryResponse

router = APIRouter(prefix="/api", tags=["actors"])


@router.get("/actors/search", response_model=PaginatedActorsResponse)
async def search_actors(
    q: str = Query(..., description="Search query for actor name"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Search for actors by name"""
    try:
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Search in both cast and crew tables
        cast_query = (
            db.query(Cast.person_id, Cast.name, Cast.profile_path)
            .filter(Cast.name.ilike(f"%{q}%"))
            .group_by(Cast.person_id, Cast.name, Cast.profile_path)
        )
        
        crew_query = (
            db.query(Crew.person_id, Crew.name, Crew.profile_path)
            .filter(Crew.name.ilike(f"%{q}%"))
            .group_by(Crew.person_id, Crew.name, Crew.profile_path)
        )
        
        # Union the queries and get unique actors
        combined_query = cast_query.union(crew_query)
        
        # Get total count
        total = combined_query.count()
        
        # Get paginated results
        actors_data = combined_query.offset(offset).limit(per_page).all()
        
        # Convert to response format
        actors = []
        for person_id, name, profile_path in actors_data:
            # Count movies for this actor
            cast_count = db.query(func.count(Cast.movie_id.distinct())).filter(Cast.person_id == person_id).scalar()
            crew_count = db.query(func.count(Crew.movie_id.distinct())).filter(Crew.person_id == person_id).scalar()
            movie_count = cast_count + crew_count
            
            actors.append(ActorResponse(
                person_id=person_id,
                name=name,
                profile_path=profile_path,
                movie_count=movie_count
            ))
        
        # Calculate pagination info
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        return PaginatedActorsResponse(
            actors=actors,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/actors/{person_id}", response_model=ActorDetailResponse)
async def get_actor_detail(
    person_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about an actor"""
    try:
        # Get actor basic info from cast or crew
        actor_info = (
            db.query(Cast.person_id, Cast.name, Cast.profile_path)
            .filter(Cast.person_id == person_id)
            .first()
        )
        
        if not actor_info:
            actor_info = (
                db.query(Crew.person_id, Crew.name, Crew.profile_path)
                .filter(Crew.person_id == person_id)
                .first()
            )
        
        if not actor_info:
            raise HTTPException(status_code=404, detail="Actor not found")
        
        # Get movies where this person was cast
        cast_movies = (
            db.query(Cast, Movie)
            .join(Movie, Cast.movie_id == Movie.id)
            .filter(Cast.person_id == person_id)
            .order_by(desc(Movie.year))
            .all()
        )
        
        # Get movies where this person was crew
        crew_movies = (
            db.query(Crew, Movie)
            .join(Movie, Crew.movie_id == Movie.id)
            .filter(Crew.person_id == person_id)
            .order_by(desc(Movie.year))
            .all()
        )
        
        # Convert to response format
        cast_roles = []
        for cast, movie in cast_movies:
            cast_roles.append({
                "movie": MovieSummaryResponse(
                    id=movie.id,
                    title=movie.title,
                    year=movie.year,
                    genre=movie.genre,
                    rating=movie.rating,
                    poster_url=movie.poster_url
                ),
                "character": cast.character,
                "order": cast.order
            })
        
        crew_roles = []
        for crew, movie in crew_movies:
            crew_roles.append({
                "movie": MovieSummaryResponse(
                    id=movie.id,
                    title=movie.title,
                    year=movie.year,
                    genre=movie.genre,
                    rating=movie.rating,
                    poster_url=movie.poster_url
                ),
                "job": crew.job,
                "department": crew.department
            })
        
        return ActorDetailResponse(
            person_id=actor_info.person_id,
            name=actor_info.name,
            profile_path=actor_info.profile_path,
            cast_roles=cast_roles,
            crew_roles=crew_roles
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/movies/{movie_id}/cast", response_model=List[ActorResponse])
async def get_movie_cast(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get cast members for a specific movie"""
    try:
        # Check if movie exists
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Get cast members
        cast_members = (
            db.query(Cast)
            .filter(Cast.movie_id == movie_id)
            .order_by(Cast.order.asc().nulls_last())
            .all()
        )
        
        # Convert to response format
        actors = []
        for cast in cast_members:
            # Count total movies for this actor
            movie_count = db.query(func.count(Cast.movie_id.distinct())).filter(Cast.person_id == cast.person_id).scalar()
            
            actors.append(ActorResponse(
                person_id=cast.person_id,
                name=cast.name,
                profile_path=cast.profile_path,
                movie_count=movie_count,
                character=cast.character,
                order=cast.order
            ))
        
        return actors
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/movies/{movie_id}/crew")
async def get_movie_crew(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get crew members for a specific movie"""
    try:
        # Check if movie exists
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Get crew members grouped by department
        crew_members = (
            db.query(Crew)
            .filter(Crew.movie_id == movie_id)
            .order_by(Crew.department, Crew.job)
            .all()
        )
        
        # Group by department
        departments = {}
        for crew in crew_members:
            dept = crew.department or "Other"
            if dept not in departments:
                departments[dept] = []
            
            # Count total movies for this person
            movie_count = db.query(func.count(Crew.movie_id.distinct())).filter(Crew.person_id == crew.person_id).scalar()
            
            departments[dept].append({
                "person_id": crew.person_id,
                "name": crew.name,
                "job": crew.job,
                "profile_path": crew.profile_path,
                "movie_count": movie_count
            })
        
        return departments
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")