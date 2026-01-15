"""
Analytics and activity logging system
"""
import time
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from fastapi import Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models import User, Movie, Review
import logging

# Configure logging for analytics
logging.basicConfig(level=logging.INFO)
analytics_logger = logging.getLogger("cinema-analytics")

class ActivityLogger:
    """Handles activity logging for analytics"""
    
    def __init__(self):
        self.logger = analytics_logger
    
    async def log_activity(self, event_data: Dict[str, Any]):
        """Log activity event"""
        try:
            # Add timestamp if not present
            if 'timestamp' not in event_data:
                event_data['timestamp'] = datetime.utcnow().isoformat()
            
            # Log as structured JSON
            self.logger.info(json.dumps(event_data))
        except Exception as e:
            # Don't let logging errors break the application
            self.logger.error(f"Failed to log activity: {str(e)}")
    
    async def log_api_request(
        self,
        request: Request,
        response_status: int,
        response_time: float,
        user_id: Optional[int] = None
    ):
        """Log API request for analytics"""
        event_data = {
            "source": "cinema-api",
            "event_type": "api_request",
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "status_code": response_status,
            "response_time": response_time,
            "user_agent": request.headers.get("User-Agent"),
            "ip_address": request.client.host if request.client else None,
            "user_id": user_id
        }
        await self.log_activity(event_data)
    
    async def log_search_query(
        self,
        query: str,
        results_count: int,
        user_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """Log search query for analytics"""
        event_data = {
            "source": "cinema-api",
            "event_type": "search",
            "search_query": query,
            "results_count": results_count,
            "user_id": user_id,
            "filters": filters or {}
        }
        await self.log_activity(event_data)
    
    async def log_movie_view(
        self,
        movie_id: int,
        user_id: Optional[int] = None
    ):
        """Log movie view for analytics"""
        event_data = {
            "source": "cinema-api",
            "event_type": "movie_view",
            "movie_id": movie_id,
            "user_id": user_id
        }
        await self.log_activity(event_data)
    
    async def log_review_action(
        self,
        action: str,  # create, update, delete
        movie_id: int,
        user_id: int,
        rating: Optional[int] = None
    ):
        """Log review action for analytics"""
        event_data = {
            "source": "cinema-api",
            "event_type": "review_action",
            "action": action,
            "movie_id": movie_id,
            "user_id": user_id,
            "rating": rating
        }
        await self.log_activity(event_data)


class AnalyticsService:
    """Service for generating analytics data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_analytics(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get user activity analytics"""
        
        # Base query for users
        user_query = self.db.query(User)
        
        # Apply date filters if provided
        if date_from:
            user_query = user_query.filter(User.created_at >= date_from)
        if date_to:
            user_query = user_query.filter(User.created_at <= date_to)
        
        # Get user counts
        total_users = self.db.query(func.count(User.id)).scalar()
        new_users = user_query.count() if date_from or date_to else 0
        
        # Get today's registrations
        today = datetime.utcnow().date()
        today_registrations = self.db.query(func.count(User.id)).filter(
            func.date(User.created_at) == today
        ).scalar()
        
        # Get admin users count
        admin_users = self.db.query(func.count(User.id)).filter(User.is_admin == True).scalar()
        
        return {
            "total_users": total_users,
            "new_users_period": new_users,
            "new_registrations_today": today_registrations,
            "admin_users": admin_users,
            "active_users_today": 0,  # Would need session tracking for this
            "average_session_duration": 0.0  # Would need session tracking for this
        }
    
    def get_movie_analytics(self) -> Dict[str, Any]:
        """Get movie popularity and rating analytics"""
        
        # Most reviewed movies
        most_reviewed = self.db.query(
            Movie.id,
            Movie.title,
            func.count(Review.id).label('review_count'),
            func.avg(Review.rating).label('avg_rating')
        ).outerjoin(Review).group_by(Movie.id, Movie.title).order_by(
            desc(func.count(Review.id))
        ).limit(10).all()
        
        # Highest rated movies (with at least 1 review)
        highest_rated = self.db.query(
            Movie.id,
            Movie.title,
            Movie.rating.label('original_rating'),
            func.avg(Review.rating).label('user_rating'),
            func.count(Review.id).label('review_count')
        ).join(Review).group_by(Movie.id, Movie.title, Movie.rating).having(
            func.count(Review.id) >= 1
        ).order_by(desc(func.avg(Review.rating))).limit(10).all()
        
        # Genre popularity
        genre_stats = self.db.query(
            Movie.genre,
            func.count(Movie.id).label('movie_count'),
            func.count(Review.id).label('total_reviews')
        ).outerjoin(Review).group_by(Movie.genre).order_by(
            desc(func.count(Review.id))
        ).limit(10).all()
        
        return {
            "most_reviewed_movies": [
                {
                    "id": movie.id,
                    "title": movie.title,
                    "review_count": movie.review_count,
                    "average_rating": float(movie.avg_rating) if movie.avg_rating else None
                }
                for movie in most_reviewed
            ],
            "highest_rated_movies": [
                {
                    "id": movie.id,
                    "title": movie.title,
                    "original_rating": movie.original_rating,
                    "user_rating": float(movie.user_rating) if movie.user_rating else None,
                    "review_count": movie.review_count
                }
                for movie in highest_rated
            ],
            "genre_popularity": [
                {
                    "genre": genre.genre,
                    "movie_count": genre.movie_count,
                    "total_reviews": genre.total_reviews
                }
                for genre in genre_stats if genre.genre
            ]
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        
        # Database stats
        total_movies = self.db.query(func.count(Movie.id)).scalar()
        total_reviews = self.db.query(func.count(Review.id)).scalar()
        total_users = self.db.query(func.count(User.id)).scalar()
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow().date()
        recent_reviews = self.db.query(func.count(Review.id)).filter(
            func.date(Review.created_at) >= week_ago
        ).scalar()
        
        recent_users = self.db.query(func.count(User.id)).filter(
            func.date(User.created_at) >= week_ago
        ).scalar()
        
        return {
            "database_stats": {
                "total_movies": total_movies,
                "total_reviews": total_reviews,
                "total_users": total_users
            },
            "recent_activity": {
                "reviews_last_7_days": recent_reviews,
                "new_users_last_7_days": recent_users
            },
            "api_response_times": {},  # Would be populated from logs
            "error_rates": {},  # Would be populated from logs
            "active_sessions": 0  # Would need session tracking
        }


# Global activity logger instance
activity_logger = ActivityLogger()