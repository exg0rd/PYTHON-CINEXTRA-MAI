"""
Admin API endpoints for analytics and system management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import date, datetime, timedelta

from ..db.database import get_db
from ..db.models import User, Movie, Review
from ..core.analytics import AnalyticsService, activity_logger
from ..api.auth import get_current_user
from ..core.logging import logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to ensure user is admin"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    # Log admin access
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_access",
        "user_id": current_user.id,
        "admin_action": "access_check"
    })
    
    return current_user


@router.get("/stats/overview")
async def get_overview_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Получение общей статистики для админ панели"""
    
    # Общие счетчики
    total_movies = db.query(Movie).count()
    total_users = db.query(User).count()
    total_reviews = db.query(Review).count()
    
    # Статистика за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    new_users_30d = db.query(User).filter(User.created_at >= thirty_days_ago).count()
    new_reviews_30d = db.query(Review).filter(Review.created_at >= thirty_days_ago).count()
    
    # Средний рейтинг
    avg_rating = db.query(func.avg(Review.rating)).scalar() or 0
    
    # Статистика видео
    movies_with_video = db.query(Movie).filter(Movie.video_file_id.isnot(None)).count()
    processing_videos = db.query(Movie).filter(Movie.processing_status == "processing").count()
    failed_videos = db.query(Movie).filter(Movie.processing_status == "failed").count()
    
    return {
        "total_movies": total_movies,
        "total_users": total_users,
        "total_reviews": total_reviews,
        "new_users_30d": new_users_30d,
        "new_reviews_30d": new_reviews_30d,
        "average_rating": round(float(avg_rating), 2),
        "movies_with_video": movies_with_video,
        "processing_videos": processing_videos,
        "failed_videos": failed_videos
    }


@router.get("/movies/video-status")
async def get_movies_video_status(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Получение списка фильмов с информацией о статусе видео"""
    
    query = db.query(Movie)
    
    # Filter by search query
    if search:
        search_term = f"%{search}%"
        query = query.filter(Movie.title.ilike(search_term))
    
    if status:
        if status == "no_video":
            query = query.filter(Movie.video_file_id.is_(None))
        else:
            query = query.filter(Movie.processing_status == status)
    
    # Order by title for consistent results
    query = query.order_by(Movie.title)
    
    total = query.count()
    movies = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "movies": [
            {
                "id": movie.id,
                "title": movie.title,
                "year": movie.year,
                "video_file_id": movie.video_file_id,
                "processing_status": movie.processing_status,
                "available_qualities": movie.available_qualities or [],
                "duration_seconds": movie.duration_seconds,
                "hls_manifest_url": movie.hls_manifest_url
            }
            for movie in movies
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/movies/{movie_id}/upload-video")
async def admin_upload_video(
    movie_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Загрузка видеофайла для фильма через админ панель"""
    logger.info(f"Admin {admin_user.username} uploading video for movie {movie_id}")
    
    from ..api.upload import upload_video
    return await upload_video(movie_id, file, background_tasks, db, admin_user)


@router.get("/upload/status/{task_id}")
async def admin_get_upload_status(
    task_id: str,
    admin_user: User = Depends(get_admin_user)
):
    """Получение статуса обработки видео"""
    from ..api.upload import get_upload_status
    return await get_upload_status(task_id, admin_user)


@router.delete("/movies/{movie_id}/video")
async def admin_delete_video(
    movie_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Удаление видеофайла фильма"""
    logger.info(f"Admin {admin_user.username} deleting video for movie {movie_id}")
    
    from ..api.upload import delete_video
    return await delete_video(movie_id, db, admin_user)


@router.post("/movies/{movie_id}/reprocess-video")
async def admin_reprocess_video(
    movie_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Повторная обработка видео"""
    logger.info(f"Admin {admin_user.username} reprocessing video for movie {movie_id}")
    
    from ..api.upload import reprocess_video
    return await reprocess_video(movie_id, background_tasks, db, admin_user)


@router.get("/analytics/users")
async def get_user_analytics(
    date_from: Optional[date] = Query(None, description="Start date for filtering"),
    date_to: Optional[date] = Query(None, description="End date for filtering"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get user activity analytics for admin dashboard"""
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "view_user_analytics",
        "filters": {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None
        }
    })
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_user_analytics(date_from, date_to)


@router.get("/analytics/movies")
async def get_movie_analytics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get movie popularity and rating analytics"""
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "view_movie_analytics"
    })
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_movie_analytics()


@router.get("/analytics/system")
async def get_system_metrics(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get system performance metrics"""
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "view_system_metrics"
    })
    
    analytics_service = AnalyticsService(db)
    return analytics_service.get_system_metrics()


@router.post("/users/{user_id}/make-admin")
async def make_user_admin(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Make a user an admin (admin only)"""
    
    # Find the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="User is already an admin")
    
    # Update user to admin
    user.is_admin = True
    db.commit()
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "make_user_admin",
        "target_user_id": user_id
    })
    
    return {"message": f"User {user.username} is now an admin"}


@router.delete("/users/{user_id}/remove-admin")
async def remove_user_admin(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Remove admin privileges from a user (admin only)"""
    
    # Find the user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_admin:
        raise HTTPException(status_code=400, detail="User is not an admin")
    
    # Prevent removing admin from self
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove admin privileges from yourself")
    
    # Update user to remove admin
    user.is_admin = False
    db.commit()
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "remove_user_admin",
        "target_user_id": user_id
    })
    
    return {"message": f"Admin privileges removed from user {user.username}"}


@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    
    # Log admin action
    await activity_logger.log_activity({
        "source": "cinema-api",
        "event_type": "admin_action",
        "user_id": current_user.id,
        "admin_action": "list_users",
        "page": page
    })
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get users
    users = db.query(User).offset(offset).limit(per_page).all()
    total_users = db.query(User).count()
    
    return {
        "users": [user.to_dict() for user in users],
        "total": total_users,
        "page": page,
        "per_page": per_page,
        "total_pages": (total_users + per_page - 1) // per_page
    }