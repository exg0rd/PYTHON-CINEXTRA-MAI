from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Callable
import uuid
import os
import tempfile
import shutil
import asyncio

from app.db.database import get_db
from app.api.auth import get_current_admin_user
from app.db.models import Movie
from app.services.minio_service import MinIOService
from app.services.video_processing_service import VideoProcessingService
from app.workers.video_processor import process_video_task
from app.workers.celery_app import celery_app
from app.core.logging import logger

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("/video/{movie_id}")
async def upload_video(
    movie_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """
    Загрузка видеофайла для фильма с автоматическим запуском обработки
    Только для администраторов
    """
    
    # Проверяем что фильм существует
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    # Инициализируем сервисы
    minio_service = MinIOService()
    
    # Если у фильма уже есть видео, удаляем старое перед загрузкой нового
    if movie.video_file_id:
        logger.info(f"Movie {movie_id} already has video {movie.video_file_id}, will be replaced")
        try:
            # Удаляем старый видеофайл
            await minio_service.delete_object("videos", movie.video_file_id)
            # Удаляем обработанные файлы
            processed_path = f"processed-videos/{movie.video_file_id}"
            objects = await minio_service.list_objects("videos", prefix=processed_path)
            for obj in objects:
                await minio_service.delete_object("videos", obj)
            # Удаляем манифест
            if movie.hls_manifest_url:
                manifest_path = movie.hls_manifest_url
                if manifest_path.startswith("manifests/"):
                    manifest_path = manifest_path[len("manifests/"):]
                await minio_service.delete_object("manifests", manifest_path)
        except Exception as e:
            logger.warning(f"Failed to delete old video files: {e}")
    
    # Валидация файла
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Проверяем размер файла (максимум 10GB)
    max_size = 10 * 1024 * 1024 * 1024  # 10GB
    if file.size and file.size > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10GB)")
    
    temp_file = None
    
    try:
        logger.info(f"Starting video upload for movie {movie_id}, file: {file.filename}")
        
        # Создаем временный файл
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
        
        # Читаем и сохраняем файл по частям
        chunk_size = 8192
        total_size = 0
        
        while chunk := await file.read(chunk_size):
            temp_file.write(chunk)
            total_size += len(chunk)
            
            # Проверяем размер во время загрузки
            if total_size > max_size:
                temp_file.close()
                os.unlink(temp_file.name)
                raise HTTPException(status_code=400, detail="File too large (max 10GB)")
        
        temp_file.close()
        
        # Валидируем видеофайл
        video_service = VideoProcessingService(minio_service)
        
        if not video_service.validate_video_file(temp_file.name):
            raise HTTPException(status_code=400, detail="Invalid video file")
        
        # Генерируем уникальный ID для файла
        file_id = str(uuid.uuid4())
        
        logger.info(f"Uploading file to MinIO: bucket=videos, file_id={file_id}, temp_file={temp_file.name}")
        
        # Загружаем файл в MinIO
        try:
            await minio_service.upload_file("videos", file_id, temp_file.name)
            logger.info(f"Successfully uploaded file to MinIO: {file_id}")
        except Exception as upload_error:
            logger.error(f"Failed to upload file to MinIO: {upload_error}")
            raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(upload_error)}")
        
        # Обновляем запись фильма
        movie.video_file_id = file_id
        movie.processing_status = "queued"
        db.commit()
        
        logger.info(f"Updated movie {movie_id} with file_id {file_id}")
        
        # Запускаем обработку видео в фоне (объединенная задача)
        task = process_video_task.delay(file_id, movie_id)
        
        logger.info(f"Video uploaded and processing started for movie {movie_id}, task ID: {task.id}")
        
        # Очищаем временный файл после успешной загрузки
        try:
            os.unlink(temp_file.name)
            logger.info(f"Cleaned up temp file: {temp_file.name}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up temp file: {cleanup_error}")
        
        return {
            "message": "Video uploaded successfully, processing started",
            "file_id": file_id,
            "task_id": task.id,
            "status": "queued"
        }
        
    except HTTPException:
        # Clean up temp file on HTTP errors
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        raise
    except Exception as e:
        # Clean up temp file on other errors
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)
        logger.error(f"Error uploading video: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload video")


@router.get("/status/{task_id}")
async def get_upload_status(
    task_id: str,
    admin_user = Depends(get_current_admin_user)
):
    """Получение статуса обработки видео"""
    
    try:
        # Получаем информацию о задаче
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "status": "processing",
                "progress": task.info.get("progress", 0),
                "message": task.info.get("status", "Processing..."),
                "current_step": task.info.get("current_step", ""),
                "overall_step": task.info.get("overall_step", "")
            }
        elif task.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "status": "completed",
                "result": task.result
            }
        else:  # FAILURE
            response = {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get task status")


@router.post("/batch")
async def upload_video_batch(
    files: list[UploadFile] = File(...),
    movie_ids: list[int] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """
    Пакетная загрузка видеофайлов
    Только для администраторов
    """
    
    if not movie_ids or len(files) != len(movie_ids):
        raise HTTPException(
            status_code=400, 
            detail="Number of files must match number of movie IDs"
        )
    
    results = []
    
    for file, movie_id in zip(files, movie_ids):
        try:
            # Используем существующий endpoint для каждого файла
            result = await upload_video(movie_id, file, background_tasks, db, admin_user)
            results.append({
                "movie_id": movie_id,
                "filename": file.filename,
                "status": "success",
                "result": result
            })
            
        except HTTPException as e:
            results.append({
                "movie_id": movie_id,
                "filename": file.filename,
                "status": "error",
                "error": e.detail
            })
        except Exception as e:
            results.append({
                "movie_id": movie_id,
                "filename": file.filename,
                "status": "error", 
                "error": str(e)
            })
    
    return {
        "message": f"Processed {len(files)} files",
        "results": results
    }


@router.delete("/video/{movie_id}")
async def delete_video(
    movie_id: int,
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """Удаление видеофайла фильма"""
    
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id:
        raise HTTPException(status_code=400, detail="Movie has no video file")
    
    try:
        minio_service = MinIOService()
        
        # Удаляем исходный файл
        await minio_service.delete_object("videos", movie.video_file_id)
        
        # Удаляем обработанные файлы
        processed_objects = await minio_service.list_objects("videos", f"processed-videos/{movie.video_file_id}/")
        for obj in processed_objects:
            await minio_service.delete_object("videos", obj)
        
        # Удаляем превью
        thumbnail_objects = await minio_service.list_objects("thumbnails", f"{movie.video_file_id}/")
        for obj in thumbnail_objects:
            await minio_service.delete_object("thumbnails", obj)
        
        # Удаляем манифесты
        manifest_objects = await minio_service.list_objects("manifests", f"{movie.video_file_id}/")
        for obj in manifest_objects:
            await minio_service.delete_object("manifests", obj)
        
        # Обновляем запись в БД
        movie.video_file_id = None
        movie.processing_status = None
        movie.available_qualities = []
        movie.hls_manifest_url = None
        movie.duration_seconds = None
        db.commit()
        
        logger.info(f"Deleted video for movie {movie_id}")
        
        return {"message": "Video deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting video: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete video")


@router.post("/reprocess/{movie_id}")
async def reprocess_video(
    movie_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    """Повторная обработка видео"""
    
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    if not movie.video_file_id:
        raise HTTPException(status_code=400, detail="Movie has no video file")
    
    try:
        # Обновляем статус
        movie.processing_status = "queued"
        db.commit()
        
        # Запускаем обработку
        task = process_video_task.delay(movie.video_file_id, movie_id)
        
        logger.info(f"Reprocessing video for movie {movie_id}, task ID: {task.id}")
        
        return {
            "message": "Video reprocessing started",
            "task_id": task.id,
            "status": "queued"
        }
        
    except Exception as e:
        logger.error(f"Error reprocessing video: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reprocess video")