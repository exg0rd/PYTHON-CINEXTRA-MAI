from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from typing import Optional
import math

from ..db.database import get_db
from ..db.models import Review, Movie, User
from .models import ReviewCreate, ReviewUpdate, ReviewResponse, PaginatedReviews
from .auth import get_current_user
from .exceptions import MovieNotFoundError, DatabaseConnectionError

router = APIRouter(prefix="/api", tags=["reviews"])


@router.get("/movies/{movie_id}/reviews", response_model=PaginatedReviews)
async def get_movie_reviews(
    movie_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get paginated reviews for a specific movie"""
    try:
        # Validate movie_id
        if movie_id < 1:
            raise HTTPException(status_code=422, detail="Movie ID must be a positive integer")
        
        # Check if movie exists
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise MovieNotFoundError(movie_id)
        
        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=422, detail="Page number must be greater than 0")
        if per_page < 1 or per_page > 100:
            raise HTTPException(status_code=422, detail="Items per page must be between 1 and 100")
        
        # Calculate offset
        offset = (page - 1) * per_page
        
        # Get total count of reviews for this movie
        total = db.query(func.count(Review.id)).filter(Review.movie_id == movie_id).scalar()
        
        # Get reviews for current page with user information
        reviews = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.movie_id == movie_id)
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )
        
        # Calculate pagination info
        total_pages = math.ceil(total / per_page) if total > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        # Convert to response models
        review_responses = [ReviewResponse.model_validate(review) for review in reviews]
        
        return PaginatedReviews(
            reviews=review_responses,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    except MovieNotFoundError:
        raise
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        raise DatabaseConnectionError(str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/movies/{movie_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_movie_review(
    movie_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new review for a movie (authenticated users only)"""
    try:
        # Validate movie_id
        if movie_id < 1:
            raise HTTPException(status_code=422, detail="Movie ID must be a positive integer")
        
        # Check if movie exists
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise MovieNotFoundError(movie_id)
        
        # Check if user already has a review for this movie
        existing_review = (
            db.query(Review)
            .filter(Review.user_id == current_user.id, Review.movie_id == movie_id)
            .first()
        )
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this movie. Use PUT to update your review."
            )
        
        # Create new review
        new_review = Review(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=review_data.rating,
            review_text=review_data.review_text
        )
        
        db.add(new_review)
        db.commit()
        db.refresh(new_review)
        
        # Load the user relationship for the response
        review_with_user = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.id == new_review.id)
            .first()
        )
        
        return ReviewResponse.model_validate(review_with_user)
    
    except MovieNotFoundError:
        raise
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        if "unique_user_movie_review" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this movie"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review creation failed"
            )
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseConnectionError(str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    review_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing review (only by the review author)"""
    try:
        # Validate review_id
        if review_id < 1:
            raise HTTPException(status_code=422, detail="Review ID must be a positive integer")
        
        # Get the review with user information
        review = (
            db.query(Review)
            .options(joinedload(Review.user))
            .filter(Review.id == review_id)
            .first()
        )
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Check if current user is the author of the review
        if review.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own reviews"
            )
        
        # Update review fields if provided
        if review_data.rating is not None:
            review.rating = review_data.rating
        
        if review_data.review_text is not None:
            review.review_text = review_data.review_text
        
        db.commit()
        db.refresh(review)
        
        return ReviewResponse.model_validate(review)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseConnectionError(str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a review (only by the review author)"""
    try:
        # Validate review_id
        if review_id < 1:
            raise HTTPException(status_code=422, detail="Review ID must be a positive integer")
        
        # Get the review
        review = db.query(Review).filter(Review.id == review_id).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Check if current user is the author of the review
        if review.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own reviews"
            )
        
        # Delete the review
        db.delete(review)
        db.commit()
        
        return None
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise DatabaseConnectionError(str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")