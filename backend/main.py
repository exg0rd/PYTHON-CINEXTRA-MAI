from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.api.movies import router as movies_router
from app.api.auth import router as auth_router
from app.api.reviews import router as reviews_router
from app.api.admin import router as admin_router
from app.api.actors import router as actors_router
from app.api.upload import router as upload_router
from app.api.stream import router as stream_router
from app.middleware.analytics import AnalyticsMiddleware
from app.api.exceptions import (
    validation_exception_handler,
    cinema_api_exception_handler,
    general_exception_handler,
    CinemaAPIException
)
import os

app = FastAPI(title="Online Cinema API", version="1.0.0")

# Add analytics middleware
app.add_middleware(AnalyticsMiddleware)

# Configure CORS for different environments
allowed_origins = [
    "http://localhost:3000",  # Next.js development
    "http://127.0.0.1:3000",  # Alternative localhost
]

# Add production origins if specified
production_origin = os.getenv("FRONTEND_URL")
if production_origin:
    allowed_origins.append(production_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(CinemaAPIException, cinema_api_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(movies_router)
app.include_router(auth_router)
app.include_router(reviews_router)
app.include_router(admin_router)
app.include_router(actors_router)
app.include_router(upload_router)
app.include_router(stream_router)

@app.get("/")
async def root():
    return {"message": "Online Cinema API", "version": "1.0.0"}