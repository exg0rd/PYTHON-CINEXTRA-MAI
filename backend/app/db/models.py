from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class Movie(Base):
    """SQLAlchemy model for movies"""
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    year = Column(Integer, nullable=True, index=True)
    genre = Column(String(100), nullable=True, index=True)
    director = Column(String(255), nullable=True)
    rating = Column(Float, nullable=True)
    duration = Column(Integer, nullable=True)  # in minutes
    release_date = Column(Date, nullable=True)
    poster_url = Column(String(500), nullable=True)
    imdb_id = Column(String(20), nullable=True, unique=True)
    budget = Column(Integer, nullable=True)
    revenue = Column(Integer, nullable=True)
    popularity = Column(Float, nullable=True)
    vote_count = Column(Integer, nullable=True)
    
    # Video streaming fields
    video_file_id = Column(String(255), nullable=True)  # UUID of video file in MinIO
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    available_qualities = Column(JSON, default=list)  # ["480p", "720p", "1080p", "4k"]
    hls_manifest_url = Column(String(500), nullable=True)  # URL to HLS master playlist
    duration_seconds = Column(Integer, nullable=True)  # Duration in seconds from video processing
    
    # Subtitles and audio tracks
    subtitles = Column(JSON, default=list)  # [{"language": "en", "label": "English", "url": "..."}]
    audio_tracks = Column(JSON, default=list)  # [{"language": "en", "label": "English", "default": true}]
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reviews = relationship("Review", back_populates="movie", cascade="all, delete-orphan")
    cast = relationship("Cast", back_populates="movie", cascade="all, delete-orphan")
    crew = relationship("Crew", back_populates="movie", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Movie(id={self.id}, title='{self.title}', year={self.year})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'year': self.year,
            'genre': self.genre,
            'director': self.director,
            'rating': self.rating,
            'duration': self.duration,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'poster_url': self.poster_url,
            'imdb_id': self.imdb_id,
            'budget': self.budget,
            'revenue': self.revenue,
            'popularity': self.popularity,
            'vote_count': self.vote_count,
            'video_file_id': self.video_file_id,
            'processing_status': self.processing_status,
            'available_qualities': self.available_qualities or [],
            'hls_manifest_url': self.hls_manifest_url,
            'duration_seconds': self.duration_seconds,
            'subtitles': self.subtitles or [],
            'audio_tracks': self.audio_tracks or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class User(Base):
    """SQLAlchemy model for users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # New admin field
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_admin={self.is_admin})>"

    def to_dict(self):
        """Convert model to dictionary (excluding password_hash)"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Review(Base):
    """SQLAlchemy model for movie reviews"""
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-10 scale
    review_text = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_review'),
    )

    def __repr__(self):
        return f"<Review(id={self.id}, user_id={self.user_id}, movie_id={self.movie_id}, rating={self.rating})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'movie_id': self.movie_id,
            'rating': self.rating,
            'review_text': self.review_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user': self.user.to_dict() if self.user else None
        }


class Cast(Base):
    """SQLAlchemy model for movie cast members"""
    __tablename__ = "cast"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(Integer, nullable=False, index=True)  # TMDb person ID
    name = Column(String(255), nullable=False, index=True)
    character = Column(String(500), nullable=True)
    order = Column(Integer, nullable=True)  # Order in cast list
    profile_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    movie = relationship("Movie", back_populates="cast")

    def __repr__(self):
        return f"<Cast(id={self.id}, movie_id={self.movie_id}, name='{self.name}', character='{self.character}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'person_id': self.person_id,
            'name': self.name,
            'character': self.character,
            'order': self.order,
            'profile_path': self.profile_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Crew(Base):
    """SQLAlchemy model for movie crew members"""
    __tablename__ = "crew"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id", ondelete="CASCADE"), nullable=False, index=True)
    person_id = Column(Integer, nullable=False, index=True)  # TMDb person ID
    name = Column(String(255), nullable=False, index=True)
    job = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True, index=True)
    profile_path = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    movie = relationship("Movie", back_populates="crew")

    def __repr__(self):
        return f"<Crew(id={self.id}, movie_id={self.movie_id}, name='{self.name}', job='{self.job}')>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'movie_id': self.movie_id,
            'person_id': self.person_id,
            'name': self.name,
            'job': self.job,
            'department': self.department,
            'profile_path': self.profile_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }