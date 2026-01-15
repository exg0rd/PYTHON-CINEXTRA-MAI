from celery import Celery
import os

# Создание Celery приложения
celery_app = Celery(
    "video_processing",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    include=["app.workers.video_processor"]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.workers.video_processor.process_video": {"queue": "video_processing"},
        "app.workers.video_processor.generate_thumbnails": {"queue": "thumbnails"},
        "app.workers.video_processor.cleanup_temp_files": {"queue": "cleanup"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # 1 hour
    task_soft_time_limit=3600,  # 1 hour soft limit
    task_time_limit=7200,  # 2 hours hard limit
)