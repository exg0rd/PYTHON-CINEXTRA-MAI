#!/usr/bin/env python3
"""
Database seeding functionality for movie data
"""
import logging
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from .database import SessionLocal, create_tables, drop_tables, engine
from .models import Movie
from ..core.csv_parser import MovieCSVParser, CSVParsingError
from ..models.movie import MovieData

logger = logging.getLogger(__name__)


class DatabaseSeeder:
    """Handle database seeding operations"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.csv_parser = MovieCSVParser(batch_size=batch_size)
    
    def init_database(self, drop_existing: bool = False):
        """Initialize database tables"""
        try:
            if drop_existing:
                logger.info("Dropping existing tables...")
                drop_tables()
            
            logger.info("Creating database tables...")
            create_tables()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _movie_data_to_model(self, movie_data: MovieData) -> Movie:
        """Convert MovieData to SQLAlchemy Movie model"""
        return Movie(
            title=movie_data.title,
            description=movie_data.description,
            year=movie_data.year,
            genre=movie_data.genre,
            director=movie_data.director,
            rating=movie_data.rating,
            duration=movie_data.duration,
            release_date=movie_data.release_date,
            poster_url=movie_data.poster_url,
            imdb_id=movie_data.imdb_id,
            budget=movie_data.budget,
            revenue=movie_data.revenue,
            popularity=movie_data.popularity,
            vote_count=movie_data.vote_count
        )
    
    def seed_from_csv(self, csv_file: Path, skip_duplicates: bool = True) -> dict:
        """Seed database from CSV file"""
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_file}")
        
        stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'batches_processed': 0
        }
        
        try:
            logger.info(f"Starting database seeding from: {csv_file}")
            
            # Process CSV in batches
            for batch_num, movie_batch in enumerate(self.csv_parser.parse_csv_batch(csv_file)):
                stats['batches_processed'] += 1
                batch_inserted = 0
                batch_skipped = 0
                batch_errors = 0
                
                # Create database session
                db = SessionLocal()
                
                try:
                    for movie_data in movie_batch:
                        stats['total_processed'] += 1
                        
                        try:
                            # Check for existing movie by IMDB ID or title+year
                            existing_movie = None
                            if movie_data.imdb_id:
                                existing_movie = db.query(Movie).filter(
                                    Movie.imdb_id == movie_data.imdb_id
                                ).first()
                            
                            if not existing_movie and movie_data.title and movie_data.year:
                                existing_movie = db.query(Movie).filter(
                                    Movie.title == movie_data.title,
                                    Movie.year == movie_data.year
                                ).first()
                            
                            if existing_movie and skip_duplicates:
                                batch_skipped += 1
                                continue
                            
                            # Create new movie record
                            movie_model = self._movie_data_to_model(movie_data)
                            db.add(movie_model)
                            batch_inserted += 1
                            
                        except Exception as e:
                            logger.warning(f"Error processing movie '{movie_data.title}': {e}")
                            batch_errors += 1
                    
                    # Commit batch
                    db.commit()
                    
                    stats['total_inserted'] += batch_inserted
                    stats['total_skipped'] += batch_skipped
                    stats['total_errors'] += batch_errors
                    
                    logger.info(f"Batch {batch_num + 1}: {batch_inserted} inserted, "
                              f"{batch_skipped} skipped, {batch_errors} errors")
                
                except Exception as e:
                    db.rollback()
                    logger.error(f"Error processing batch {batch_num + 1}: {e}")
                    stats['total_errors'] += len(movie_batch)
                
                finally:
                    db.close()
            
            logger.info(f"Seeding complete. Total: {stats['total_processed']} processed, "
                       f"{stats['total_inserted']} inserted, {stats['total_skipped']} skipped, "
                       f"{stats['total_errors']} errors")
            
            return stats
            
        except CSVParsingError as e:
            logger.error(f"CSV parsing error: {e}")
            raise
        except Exception as e:
            logger.error(f"Database seeding error: {e}")
            raise
    
    def seed_sample_data(self) -> dict:
        """Seed database with sample movie data"""
        sample_movies = [
            MovieData(
                title="The Matrix",
                description="A computer hacker learns from mysterious rebels about the true nature of his reality.",
                year=1999,
                genre="Action",
                director="The Wachowskis",
                rating=8.2,
                duration=136,
                release_date="1999-03-30",
                poster_url="https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
                imdb_id="tt0133093"
            ),
            MovieData(
                title="Inception",
                description="Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious.",
                year=2010,
                genre="Science Fiction",
                director="Christopher Nolan",
                rating=8.4,
                duration=148,
                release_date="2010-07-15",
                poster_url="https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg",
                imdb_id="tt1375666"
            ),
            MovieData(
                title="The Godfather",
                description="The aging patriarch of an organized crime dynasty transfers control to his reluctant son.",
                year=1972,
                genre="Drama",
                director="Francis Ford Coppola",
                rating=9.2,
                duration=175,
                release_date="1972-03-14",
                poster_url="https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg",
                imdb_id="tt0068646"
            )
        ]
        
        stats = {
            'total_processed': len(sample_movies),
            'total_inserted': 0,
            'total_skipped': 0,
            'total_errors': 0
        }
        
        db = SessionLocal()
        
        try:
            for movie_data in sample_movies:
                try:
                    # Check for existing movie
                    existing_movie = db.query(Movie).filter(
                        Movie.imdb_id == movie_data.imdb_id
                    ).first()
                    
                    if existing_movie:
                        stats['total_skipped'] += 1
                        continue
                    
                    # Create new movie
                    movie_model = self._movie_data_to_model(movie_data)
                    db.add(movie_model)
                    stats['total_inserted'] += 1
                    
                except Exception as e:
                    logger.warning(f"Error inserting sample movie '{movie_data.title}': {e}")
                    stats['total_errors'] += 1
            
            db.commit()
            logger.info(f"Sample data seeded: {stats['total_inserted']} inserted, "
                       f"{stats['total_skipped']} skipped")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error seeding sample data: {e}")
            raise
        finally:
            db.close()
        
        return stats
    
    def get_database_stats(self) -> dict:
        """Get database statistics"""
        db = SessionLocal()
        
        try:
            total_movies = db.query(Movie).count()
            
            # Get year range
            year_stats = db.query(
                func.min(Movie.year),
                func.max(Movie.year)
            ).first()
            
            # Get rating stats
            rating_stats = db.query(
                func.min(Movie.rating),
                func.max(Movie.rating),
                func.avg(Movie.rating)
            ).first()
            
            # Get genre distribution (top 10)
            genre_stats = db.query(
                Movie.genre,
                func.count(Movie.id)
            ).filter(
                Movie.genre.isnot(None)
            ).group_by(Movie.genre).order_by(
                func.count(Movie.id).desc()
            ).limit(10).all()
            
            return {
                'total_movies': total_movies,
                'year_range': {
                    'earliest': year_stats[0] if year_stats[0] else None,
                    'latest': year_stats[1] if year_stats[1] else None
                },
                'rating_stats': {
                    'min': float(rating_stats[0]) if rating_stats[0] else None,
                    'max': float(rating_stats[1]) if rating_stats[1] else None,
                    'avg': float(rating_stats[2]) if rating_stats[2] else None
                },
                'top_genres': [
                    {'genre': genre, 'count': count}
                    for genre, count in genre_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            raise
        finally:
            db.close()


# CLI functions for database operations
def init_db_command(drop_existing: bool = False):
    """CLI command to initialize database"""
    seeder = DatabaseSeeder()
    seeder.init_database(drop_existing=drop_existing)


def seed_db_command(csv_file: Optional[Path] = None, sample_data: bool = False):
    """CLI command to seed database"""
    seeder = DatabaseSeeder()
    
    if sample_data:
        stats = seeder.seed_sample_data()
    elif csv_file:
        stats = seeder.seed_from_csv(csv_file)
    else:
        raise ValueError("Either csv_file or sample_data must be specified")
    
    return stats


def db_stats_command():
    """CLI command to show database statistics"""
    seeder = DatabaseSeeder()
    return seeder.get_database_stats()