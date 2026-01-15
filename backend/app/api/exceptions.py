from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class ErrorDetail(BaseModel):
    """Model for error details"""
    field: Optional[str] = None
    message: str
    type: Optional[str] = None
    input: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standardized error response model"""
    error: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    status_code: int


class CinemaAPIException(HTTPException):
    """Base exception for Cinema API"""
    def __init__(self, status_code: int, message: str, details: Optional[List[ErrorDetail]] = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)


class MovieNotFoundError(CinemaAPIException):
    """Exception for when a movie is not found"""
    def __init__(self, movie_id: int):
        super().__init__(
            status_code=404,
            message=f"Movie with ID {movie_id} not found",
            details=[ErrorDetail(field="movie_id", message=f"No movie exists with ID {movie_id}", type="not_found")]
        )


class InvalidPaginationError(CinemaAPIException):
    """Exception for invalid pagination parameters"""
    def __init__(self, message: str, field: str = None):
        details = [ErrorDetail(field=field, message=message, type="validation_error")] if field else None
        super().__init__(
            status_code=422,
            message=f"Invalid pagination parameters: {message}",
            details=details
        )


class DatabaseConnectionError(CinemaAPIException):
    """Exception for database connection issues"""
    def __init__(self, original_error: str = None):
        message = "Database connection failed"
        if original_error:
            logger.error(f"Database error: {original_error}")
        super().__init__(
            status_code=503,
            message=message,
            details=[ErrorDetail(message="Service temporarily unavailable", type="service_error")]
        )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            type=error["type"],
            input=error.get("input")
        ))
    
    error_response = ErrorResponse(
        error="Validation Error",
        message="Request validation failed",
        details=details,
        status_code=422
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


async def cinema_api_exception_handler(request: Request, exc: CinemaAPIException):
    """Handle custom Cinema API exceptions"""
    error_response = ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        details=exc.details,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    error_response = ErrorResponse(
        error="Internal Server Error",
        message="An unexpected error occurred",
        status_code=500
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )