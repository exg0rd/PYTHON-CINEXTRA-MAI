from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.db.models import Movie
from app.services.minio_service import MinIOService
from app.core.logging import logger

router = APIRouter(prefix="/api/stream", tags=["streaming"])


@router.get("/{movie_id}/playlist.m3u8")
async def stream_master_playlist(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Stream HLS master playlist for a movie"""
    
    # Get movie from database
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.hls_manifest_url:
        raise HTTPException(status_code=404, detail="Video not available for this movie")
    
    if movie.processing_status != "completed":
        raise HTTPException(status_code=503, detail=f"Video is being processed (status: {movie.processing_status})")
    
    try:
        # Get manifest from MinIO
        minio_service = MinIOService()
        
        # Remove "manifests/" prefix if present (for backward compatibility)
        manifest_path = movie.hls_manifest_url
        if manifest_path.startswith("manifests/"):
            manifest_path = manifest_path[len("manifests/"):]
        
        manifest_data = await minio_service.get_object_data("manifests", manifest_path)
        
        return Response(
            content=manifest_data,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming manifest for movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load video manifest")


@router.get("/{movie_id}/{quality}/playlist.m3u8")
async def stream_quality_playlist(
    movie_id: int,
    quality: str,
    db: Session = Depends(get_db)
):
    """Stream HLS quality-specific playlist"""
    
    # Get movie from database
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id:
        raise HTTPException(status_code=404, detail="Video not available")
    
    # Verify quality is available
    if quality not in (movie.available_qualities or []):
        raise HTTPException(status_code=404, detail=f"Quality {quality} not available")
    
    try:
        # Get quality playlist from MinIO
        minio_service = MinIOService()
        playlist_path = f"processed-videos/{movie.video_file_id}/{quality}/playlist.m3u8"
        playlist_data = await minio_service.get_object_data("videos", playlist_path)
        
        return Response(
            content=playlist_data,
            media_type="application/vnd.apple.mpegurl",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming {quality} playlist for movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load quality playlist")


@router.get("/{movie_id}/{quality}/segment_{segment_num:int}.ts")
async def stream_segment(
    movie_id: int,
    quality: str,
    segment_num: int,
    db: Session = Depends(get_db)
):
    """Stream HLS video segment"""
    
    # Get movie from database
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id:
        raise HTTPException(status_code=404, detail="Video not available")
    
    try:
        # Get segment from MinIO
        minio_service = MinIOService()
        segment_path = f"processed-videos/{movie.video_file_id}/{quality}/segment_{segment_num:03d}.ts"
        
        # Stream the segment
        segment_stream = minio_service.get_object_stream("videos", segment_path)
        
        return StreamingResponse(
            segment_stream,
            media_type="video/mp2t",
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming segment {segment_num} for movie {movie_id} quality {quality}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load video segment")


@router.get("/{movie_id}/thumbnail/{timestamp}.jpg")
async def stream_thumbnail(
    movie_id: int,
    timestamp: int,
    db: Session = Depends(get_db)
):
    """Stream video thumbnail at specific timestamp"""
    
    # Get movie from database
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id:
        raise HTTPException(status_code=404, detail="Video not available")
    
    try:
        # Get thumbnail from MinIO
        minio_service = MinIOService()
        thumbnail_path = f"{movie.video_file_id}/thumbnail_{timestamp}.jpg"
        thumbnail_data = await minio_service.get_object_data("thumbnails", thumbnail_path)
        
        return Response(
            content=thumbnail_data,
            media_type="image/jpeg",
            headers={
                "Cache-Control": "public, max-age=31536000",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"Error streaming thumbnail for movie {movie_id} at {timestamp}s: {e}")
        raise HTTPException(status_code=404, detail="Thumbnail not found")


@router.get("/{movie_id}/thumbnails")
async def get_movie_thumbnails(
    movie_id: int,
    db: Session = Depends(get_db)
):
    """Get list of available thumbnails for a movie"""
    
    # Get movie from database
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id or not movie.duration_seconds:
        return {"thumbnails": []}
    
    try:
        # Generate list of thumbnail timestamps (every 10 seconds)
        thumbnails = []
        interval = 10
        
        for timestamp in range(0, movie.duration_seconds, interval):
            thumbnails.append({
                "timestamp": timestamp,
                "url": f"/api/stream/{movie_id}/thumbnail/{timestamp}.jpg"
            })
        
        return {"thumbnails": thumbnails}
        
    except Exception as e:
        logger.error(f"Error getting thumbnails for movie {movie_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get thumbnails")
