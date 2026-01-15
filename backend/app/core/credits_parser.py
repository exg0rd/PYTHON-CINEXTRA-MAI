import csv
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..db.models import Movie, Cast, Crew

logger = logging.getLogger(__name__)


class CreditsParser:
    """Parser for credits CSV file containing cast and crew data"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        
    def parse_credits_file(self, file_path: str) -> Dict[str, int]:
        """
        Parse credits CSV file and import cast/crew data into database
        
        Args:
            file_path: Path to the credits CSV file
            
        Returns:
            Dictionary with statistics about the import
        """
        stats = {
            'movies_processed': 0,
            'cast_imported': 0,
            'crew_imported': 0,
            'errors': 0
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        movie_id = int(row['id'])
                        cast_data = row['cast']
                        crew_data = row['crew']
                        
                        # Check if movie exists in database
                        movie = self.db.query(Movie).filter(Movie.id == movie_id).first()
                        if not movie:
                            logger.warning(f"Movie with ID {movie_id} not found in database")
                            continue
                        
                        # Parse and import cast data
                        cast_count = self._import_cast_data(movie_id, cast_data)
                        stats['cast_imported'] += cast_count
                        
                        # Parse and import crew data
                        crew_count = self._import_crew_data(movie_id, crew_data)
                        stats['crew_imported'] += crew_count
                        
                        stats['movies_processed'] += 1
                        
                        # Commit every 100 movies to avoid large transactions
                        if row_num % 100 == 0:
                            self.db.commit()
                            logger.info(f"Processed {row_num} movies...")
                            
                    except Exception as e:
                        logger.error(f"Error processing row {row_num}: {str(e)}")
                        stats['errors'] += 1
                        continue
                
                # Final commit
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Error reading credits file: {str(e)}")
            self.db.rollback()
            raise
            
        return stats
    
    def _import_cast_data(self, movie_id: int, cast_json: str) -> int:
        """Import cast data for a movie"""
        if not cast_json or cast_json.strip() == '':
            return 0
            
        try:
            cast_list = json.loads(cast_json)
            cast_count = 0
            
            for cast_member in cast_list:
                try:
                    # Extract cast member data
                    person_id = cast_member.get('id')
                    name = cast_member.get('name')
                    character = cast_member.get('character')
                    order = cast_member.get('order')
                    profile_path = cast_member.get('profile_path')
                    
                    if not person_id or not name:
                        continue
                    
                    # Check if cast member already exists for this movie
                    existing_cast = (
                        self.db.query(Cast)
                        .filter(Cast.movie_id == movie_id, Cast.person_id == person_id)
                        .first()
                    )
                    
                    if existing_cast:
                        continue
                    
                    # Create new cast entry
                    cast_entry = Cast(
                        movie_id=movie_id,
                        person_id=person_id,
                        name=name,
                        character=character,
                        order=order,
                        profile_path=profile_path
                    )
                    
                    self.db.add(cast_entry)
                    cast_count += 1
                    
                except Exception as e:
                    logger.error(f"Error importing cast member for movie {movie_id}: {str(e)}")
                    continue
            
            return cast_count
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in cast data for movie {movie_id}: {str(e)}")
            return 0
    
    def _import_crew_data(self, movie_id: int, crew_json: str) -> int:
        """Import crew data for a movie"""
        if not crew_json or crew_json.strip() == '':
            return 0
            
        try:
            crew_list = json.loads(crew_json)
            crew_count = 0
            
            for crew_member in crew_list:
                try:
                    # Extract crew member data
                    person_id = crew_member.get('id')
                    name = crew_member.get('name')
                    job = crew_member.get('job')
                    department = crew_member.get('department')
                    profile_path = crew_member.get('profile_path')
                    
                    if not person_id or not name:
                        continue
                    
                    # Check if crew member already exists for this movie with same job
                    existing_crew = (
                        self.db.query(Crew)
                        .filter(
                            Crew.movie_id == movie_id, 
                            Crew.person_id == person_id,
                            Crew.job == job
                        )
                        .first()
                    )
                    
                    if existing_crew:
                        continue
                    
                    # Create new crew entry
                    crew_entry = Crew(
                        movie_id=movie_id,
                        person_id=person_id,
                        name=name,
                        job=job,
                        department=department,
                        profile_path=profile_path
                    )
                    
                    self.db.add(crew_entry)
                    crew_count += 1
                    
                except Exception as e:
                    logger.error(f"Error importing crew member for movie {movie_id}: {str(e)}")
                    continue
            
            return crew_count
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in crew data for movie {movie_id}: {str(e)}")
            return 0
    
    def clear_credits_data(self, movie_id: Optional[int] = None):
        """Clear cast and crew data for a specific movie or all movies"""
        try:
            if movie_id:
                self.db.query(Cast).filter(Cast.movie_id == movie_id).delete()
                self.db.query(Crew).filter(Crew.movie_id == movie_id).delete()
            else:
                self.db.query(Cast).delete()
                self.db.query(Crew).delete()
            
            self.db.commit()
            logger.info(f"Cleared credits data for {'movie ' + str(movie_id) if movie_id else 'all movies'}")
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error clearing credits data: {str(e)}")
            raise


def import_credits_from_csv(db_session: Session, csv_file_path: str) -> Dict[str, int]:
    """
    Convenience function to import credits from CSV file
    
    Args:
        db_session: Database session
        csv_file_path: Path to the credits CSV file
        
    Returns:
        Dictionary with import statistics
    """
    parser = CreditsParser(db_session)
    return parser.parse_credits_file(csv_file_path)