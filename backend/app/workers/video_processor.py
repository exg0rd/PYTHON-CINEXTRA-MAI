import os
import subprocess
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Dict, List
import uuid
from celery import current_task
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.db.database import get_db
from app.services.minio_service import MinIOService
from app.services.video_processing_service import VideoProcessingService
from app.db.models import Movie
from app.core.logging import logger


def run_async(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name="process_video")
def process_video_task(self, video_file_id: str, movie_id: int):
    """
    Основная задача обработки видео:
    1. Скачивание исходного файла из MinIO
    2. Транскодирование в разные качества
    3. Создание HLS манифестов
    4. Генерация превью
    5. Загрузка обработанных файлов обратно в MinIO
    """
    
    temp_dir = None
    db = next(get_db())
    
    try:
        logger.info(f"Starting video processing for file {video_file_id}, movie {movie_id}")
        
        # Обновляем статус обработки
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            raise ValueError(f"Movie {movie_id} not found")
        
        movie.processing_status = "processing"
        db.commit()
        
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp(prefix="video_processing_")
        logger.info(f"Created temp directory: {temp_dir}")
        
        # Инициализируем сервисы
        minio_service = MinIOService()
        video_service = VideoProcessingService(minio_service)
        
        # Обновляем прогресс - начинаем загрузку
        current_task.update_state(
            state="PROGRESS", 
            meta={
                "progress": 0, 
                "status": "Starting download from storage",
                "current_step": "Download",
                "overall_step": "File Download"
            }
        )
        
        # Скачиваем исходный файл с прогрессом
        input_file = os.path.join(temp_dir, "input_video")
        
        # Создаем callback для прогресса загрузки
        def download_progress_callback(progress: float):
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": int(progress * 0.1),  # 0-10% for download
                    "status": f"Downloading source file - {progress:.1f}% complete",
                    "current_step": "Download",
                    "overall_step": "File Download"
                }
            )
        
        # Simulate download progress (MinIO download is usually fast)
        download_progress_callback(0)
        run_async(minio_service.download_file("videos", video_file_id, input_file))
        download_progress_callback(100)
        
        # Получаем информацию о видео
        video_info = video_service.get_video_info(input_file)
        logger.info(f"Video info: {video_info}")
        
        # Обновляем прогресс
        current_task.update_state(
            state="PROGRESS", 
            meta={
                "progress": 10, 
                "status": "Source file downloaded and analyzed",
                "current_step": "Analysis",
                "overall_step": "Video Analysis"
            }
        )
        
        # Определяем качества для обработки на основе исходного разрешения
        qualities = video_service.determine_output_qualities(video_info)
        logger.info(f"Will process qualities: {qualities}")
        
        processed_files = {}
        total_qualities = len(qualities)
        
        # Обрабатываем каждое качество
        for i, quality in enumerate(qualities):
            logger.info(f"Processing quality: {quality}")
            
            # Создаем callback для обновления прогресса транскодирования
            def transcoding_progress_callback(ffmpeg_progress: float):
                current_task.update_state(
                    state="PROGRESS", 
                    meta={
                        "progress": int(ffmpeg_progress), 
                        "status": f"Transcoding {quality} quality - {ffmpeg_progress:.1f}% complete",
                        "current_step": f"Quality {i + 1}/{total_qualities}: {quality}",
                        "overall_step": "Video Transcoding"
                    }
                )
            
            # Обновляем статус начала транскодирования
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": 0, 
                    "status": f"Starting transcoding for {quality} quality",
                    "current_step": f"Quality {i + 1}/{total_qualities}: {quality}",
                    "overall_step": "Video Transcoding"
                }
            )
            
            # Транскодирование с мониторингом прогресса
            output_file = os.path.join(temp_dir, f"output_{quality}.mp4")
            video_service.transcode_video(
                input_file, 
                output_file, 
                quality, 
                video_info["duration"], 
                transcoding_progress_callback
            )
            
            # Создание HLS сегментов
            hls_dir = os.path.join(temp_dir, f"hls_{quality}")
            os.makedirs(hls_dir, exist_ok=True)
            
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": 0, 
                    "status": f"Creating HLS segments for {quality}",
                    "current_step": f"Quality {i + 1}/{total_qualities}: {quality}",
                    "overall_step": "HLS Segmentation"
                }
            )
            
            playlist_file = video_service.create_hls_segments(output_file, hls_dir, quality)
            
            # Загрузка HLS файлов в MinIO
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": 50, 
                    "status": f"Uploading {quality} files to storage",
                    "current_step": f"Quality {i + 1}/{total_qualities}: {quality}",
                    "overall_step": "File Upload"
                }
            )
            
            hls_files = run_async(video_service.upload_hls_files(hls_dir, video_file_id, quality, minio_service))
            processed_files[quality] = hls_files
            
            # Обновляем прогресс после завершения качества
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": 100, 
                    "status": f"Completed {quality} quality processing",
                    "current_step": f"Quality {i + 1}/{total_qualities}: {quality}",
                    "overall_step": "Quality Complete"
                }
            )
        
        # Создаем master playlist
        master_playlist = video_service.create_master_playlist(processed_files)
        master_playlist_id = str(uuid.uuid4())
        
        run_async(minio_service.upload_text(
            "manifests", 
            f"{video_file_id}/master.m3u8", 
            master_playlist
        ))
        
        # Генерируем превью
        current_task.update_state(
            state="PROGRESS", 
            meta={
                "progress": 0, 
                "status": "Starting thumbnail generation",
                "current_step": "Thumbnails",
                "overall_step": "Thumbnail Generation"
            }
        )
        
        # Создаем callback для прогресса генерации превью
        def thumbnail_progress_callback(thumbnail_progress: float):
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": int(thumbnail_progress), 
                    "status": f"Generating thumbnails - {thumbnail_progress:.1f}% complete",
                    "current_step": "Thumbnails",
                    "overall_step": "Thumbnail Generation"
                }
            )
        
        thumbnails = video_service.generate_thumbnails(
            input_file, 
            video_info["duration"], 
            10,  # interval
            thumbnail_progress_callback
        )
        thumbnail_ids = []
        
        current_task.update_state(
            state="PROGRESS", 
            meta={
                "progress": 0, 
                "status": "Uploading thumbnails to storage",
                "current_step": "Thumbnails",
                "overall_step": "Thumbnail Upload"
            }
        )
        
        for i, thumbnail_path in enumerate(thumbnails):
            thumbnail_id = f"{video_file_id}/thumbnail_{i * 10}.jpg"
            run_async(minio_service.upload_file("thumbnails", thumbnail_id, thumbnail_path))
            thumbnail_ids.append(thumbnail_id)
            
            # Update upload progress
            upload_progress = ((i + 1) / len(thumbnails)) * 100
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": int(upload_progress), 
                    "status": f"Uploading thumbnails - {upload_progress:.1f}% complete ({i + 1}/{len(thumbnails)})",
                    "current_step": "Thumbnails",
                    "overall_step": "Thumbnail Upload"
                }
            )
        
        # Обновляем запись в базе данных
        current_task.update_state(
            state="PROGRESS", 
            meta={
                "progress": 100, 
                "status": "Processing completed successfully!",
                "current_step": "Complete",
                "overall_step": "Finalization"
            }
        )
        
        movie.processing_status = "completed"
        movie.available_qualities = list(qualities)
        movie.hls_manifest_url = f"{video_file_id}/master.m3u8"
        movie.duration_seconds = int(video_info["duration"])
        db.commit()
        
        logger.info(f"Video processing completed for movie {movie_id}")
        
        # Планируем очистку временных файлов
        cleanup_temp_files.delay(temp_dir)
        
        return {
            "status": "success",
            "movie_id": movie_id,
            "processed_qualities": list(qualities),
            "master_playlist": f"manifests/{video_file_id}/master.m3u8",
            "thumbnails": thumbnail_ids,
            "duration": video_info["duration"]
        }
        
    except Exception as e:
        logger.error(f"Error processing video {video_file_id}: {str(e)}")
        
        # Обновляем статус ошибки в БД
        if 'movie' in locals():
            movie.processing_status = "failed"
            db.commit()
        
        # Очищаем временные файлы при ошибке
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Retry до 3 раз
        if self.request.retries < 3:
            logger.info(f"Retrying video processing, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (self.request.retries + 1), exc=e)
        
        raise e
    
    finally:
        db.close()


@celery_app.task(name="generate_thumbnails")
def generate_thumbnails_task(video_file_id: str, movie_id: int):
    """Отдельная задача для генерации превью (может быть запущена независимо)"""
    
    temp_dir = None
    db = next(get_db())
    
    try:
        logger.info(f"Generating thumbnails for video {video_file_id}")
        
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp(prefix="thumbnail_generation_")
        
        # Инициализируем сервисы
        minio_service = MinIOService()
        video_service = VideoProcessingService(minio_service)
        
        # Скачиваем исходный файл
        input_file = os.path.join(temp_dir, "input_video")
        run_async(minio_service.download_file("videos", video_file_id, input_file))
        
        # Получаем информацию о видео
        video_info = video_service.get_video_info(input_file)
        
        # Генерируем превью
        thumbnails = video_service.generate_thumbnails(input_file, video_info["duration"])
        
        # Загружаем превью в MinIO
        thumbnail_ids = []
        total_thumbnails = len(thumbnails)
        
        for i, thumbnail_path in enumerate(thumbnails):
            thumbnail_id = f"{video_file_id}/thumbnail_{i * 10}.jpg"
            run_async(minio_service.upload_file("thumbnails", thumbnail_id, thumbnail_path))
            thumbnail_ids.append(thumbnail_id)
            
            # Update progress
            progress = ((i + 1) / total_thumbnails) * 100
            current_task.update_state(
                state="PROGRESS", 
                meta={
                    "progress": int(progress), 
                    "status": f"Uploading thumbnail {i + 1}/{total_thumbnails}"
                }
            )
        
        logger.info(f"Generated {len(thumbnail_ids)} thumbnails for video {video_file_id}")
        
        return {
            "status": "success",
            "thumbnails": thumbnail_ids
        }
        
    except Exception as e:
        logger.error(f"Error generating thumbnails for video {video_file_id}: {str(e)}")
        raise e
    
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        db.close()


@celery_app.task(name="cleanup_temp_files")
def cleanup_temp_files(temp_dir: str):
    """Задача для очистки временных файлов"""
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")
    except Exception as e:
        logger.error(f"Error cleaning up temp directory {temp_dir}: {str(e)}")


@celery_app.task(name="process_video_batch")
def process_video_batch(video_files: List[Dict]):
    """Пакетная обработка нескольких видео"""
    results = []
    
    for video_file in video_files:
        try:
            result = process_video_task.delay(
                video_file["file_id"], 
                video_file["movie_id"]
            )
            results.append({
                "movie_id": video_file["movie_id"],
                "task_id": result.id,
                "status": "queued"
            })
        except Exception as e:
            logger.error(f"Error queuing video processing for movie {video_file['movie_id']}: {str(e)}")
            results.append({
                "movie_id": video_file["movie_id"],
                "status": "error",
                "error": str(e)
            })
    
    return results