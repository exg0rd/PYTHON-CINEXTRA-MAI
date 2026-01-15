"""
Analytics middleware for tracking API requests
"""
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.analytics import activity_logger
from app.api.auth import get_current_user_optional
from app.db.database import get_db


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests for analytics"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get user context if available
        user_id = None
        try:
            # Try to get current user from request
            # This is a simplified approach - in production you'd want more robust user detection
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # We'll skip user detection for now to avoid circular dependencies
                pass
        except Exception:
            pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log the request
        try:
            await activity_logger.log_api_request(
                request=request,
                response_status=response.status_code,
                response_time=response_time,
                user_id=user_id
            )
        except Exception as e:
            # Don't let logging errors break the application
            print(f"Analytics logging error: {e}")
        
        return response