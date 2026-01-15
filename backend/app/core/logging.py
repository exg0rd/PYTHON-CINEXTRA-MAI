"""
Centralized logging configuration for the cinema application
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'service'):
            log_entry["service"] = record.service
        
        return json.dumps(log_entry)

def setup_logging(service_name: str = "cinema-backend", log_level: str = "INFO"):
    """Setup centralized logging configuration"""
    
    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    file_handler = logging.FileHandler(logs_dir / f"{service_name}.log")
    file_handler.setFormatter(json_formatter)
    
    error_handler = logging.FileHandler(logs_dir / f"{service_name}-error.log")
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure specific loggers
    loggers = [
        "app",
        "uvicorn",
        "sqlalchemy.engine",
        "celery",
        "minio"
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level.upper()))
    
    # Reduce noise from some loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return root_logger

class ContextualLogger:
    """Logger with contextual information"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = {}
    
    def set_context(self, **kwargs):
        """Set context for all subsequent log messages"""
        self.context.update(kwargs)
    
    def clear_context(self):
        """Clear all context"""
        self.context.clear()
    
    def _log_with_context(self, level, message, **kwargs):
        """Log message with context"""
        extra = {**self.context, **kwargs}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)

class RequestLogger:
    """Logger for HTTP requests with correlation IDs"""
    
    def __init__(self):
        self.logger = ContextualLogger("app.requests")
    
    async def log_request(self, request, response, duration: float):
        """Log HTTP request details"""
        self.logger.info(
            f"{request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None
        )

class SecurityLogger:
    """Logger for security events"""
    
    def __init__(self):
        self.logger = ContextualLogger("app.security")
    
    def log_auth_attempt(self, username: str, success: bool, ip_address: str):
        """Log authentication attempt"""
        self.logger.info(
            f"Authentication {'successful' if success else 'failed'} for user {username}",
            username=username,
            success=success,
            ip_address=ip_address,
            event_type="auth_attempt"
        )
    
    def log_admin_action(self, admin_user: str, action: str, target: Optional[str] = None):
        """Log admin actions"""
        self.logger.info(
            f"Admin action: {action}",
            admin_user=admin_user,
            action=action,
            target=target,
            event_type="admin_action"
        )
    
    def log_suspicious_activity(self, description: str, **kwargs):
        """Log suspicious activity"""
        self.logger.warning(
            f"Suspicious activity: {description}",
            description=description,
            event_type="suspicious_activity",
            **kwargs
        )

class VideoProcessingLogger:
    """Logger for video processing events"""
    
    def __init__(self):
        self.logger = ContextualLogger("app.video_processing")
    
    def log_upload_start(self, movie_id: int, filename: str, file_size: int):
        """Log video upload start"""
        self.logger.info(
            f"Video upload started for movie {movie_id}",
            movie_id=movie_id,
            filename=filename,
            file_size=file_size,
            event_type="upload_start"
        )
    
    def log_processing_start(self, video_file_id: str, movie_id: int):
        """Log video processing start"""
        self.logger.info(
            f"Video processing started for movie {movie_id}",
            video_file_id=video_file_id,
            movie_id=movie_id,
            event_type="processing_start"
        )
    
    def log_processing_complete(self, video_file_id: str, movie_id: int, qualities: list, duration: float):
        """Log video processing completion"""
        self.logger.info(
            f"Video processing completed for movie {movie_id}",
            video_file_id=video_file_id,
            movie_id=movie_id,
            qualities=qualities,
            processing_duration=duration,
            event_type="processing_complete"
        )
    
    def log_processing_error(self, video_file_id: str, movie_id: int, error: str):
        """Log video processing error"""
        self.logger.error(
            f"Video processing failed for movie {movie_id}: {error}",
            video_file_id=video_file_id,
            movie_id=movie_id,
            error=error,
            event_type="processing_error"
        )

class StreamingLogger:
    """Logger for streaming events"""
    
    def __init__(self):
        self.logger = ContextualLogger("app.streaming")
    
    def log_stream_start(self, user_id: int, movie_id: int, quality: str):
        """Log stream start"""
        self.logger.info(
            f"Stream started: user {user_id}, movie {movie_id}, quality {quality}",
            user_id=user_id,
            movie_id=movie_id,
            quality=quality,
            event_type="stream_start"
        )
    
    def log_quality_change(self, user_id: int, movie_id: int, old_quality: str, new_quality: str):
        """Log quality change"""
        self.logger.info(
            f"Quality changed: user {user_id}, movie {movie_id}, {old_quality} -> {new_quality}",
            user_id=user_id,
            movie_id=movie_id,
            old_quality=old_quality,
            new_quality=new_quality,
            event_type="quality_change"
        )
    
    def log_stream_error(self, user_id: int, movie_id: int, error: str):
        """Log streaming error"""
        self.logger.error(
            f"Streaming error: user {user_id}, movie {movie_id}: {error}",
            user_id=user_id,
            movie_id=movie_id,
            error=error,
            event_type="stream_error"
        )

# Initialize logging
setup_logging()

# Create logger instances
logger = ContextualLogger("app")
request_logger = RequestLogger()
security_logger = SecurityLogger()
video_processing_logger = VideoProcessingLogger()
streaming_logger = StreamingLogger()

# Middleware for request logging
@asynccontextmanager
async def log_request_context(request, call_next):
    """Context manager for request logging"""
    import time
    import uuid
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    # Set context
    logger.set_context(request_id=request_id)
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log request
        await request_logger.log_request(request, response, duration)
        
        return response
    
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Request failed: {str(e)}", duration=duration, exception=str(e))
        raise
    
    finally:
        # Clear context
        logger.clear_context()