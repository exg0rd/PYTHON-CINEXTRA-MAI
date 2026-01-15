import pandas as pd
import json
import ast
from typing import List, Dict, Any, Optional, Generator
from pathlib import Path
import logging
from datetime import datetime

from ..models.movie import MovieData

logger = logging.getLogger(__name__)


class CSVParsingError(Exception):
    """Custom exception for CSV parsing errors"""
    pass


class MovieCSVParser:
    """Parser for movie CSV data with validation and batch processing"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.required_columns = ['title']  # Minimum required columns
        
    def _extract_genres(self, genres_str: str) -> Optional[str]:
        """Extract primary genre from genres JSON string"""
        if not genres_str or pd.isna(genres_str):
            return None
            
        try:
            # Handle string representation of list/dict
            if isinstance(genres_str, str):
                # Try to parse as JSON first
                try:
                    genres = json.loads(genres_str.replace("'", '"'))
                except json.JSONDecodeError:
                    # Try to parse as Python literal
                    try:
                        genres = ast.literal_eval(genres_str)
                    except (ValueError, SyntaxError):
                        return None
                        
                if isinstance(genres, list) and len(genres) > 0:
                    # Get first genre name
                    first_genre = genres[0]
                    if isinstance(first_genre, dict) and 'name' in first_genre:
                        return first_genre['name']
                    elif isinstance(first_genre, str):
                        return first_genre
                        
        except Exception as e:
            logger.warning(f"Error parsing genres '{genres_str}': {e}")
            
        return None
    
    def _extract_director(self, crew_str: str) -> Optional[str]:
        """Extract director from production companies or crew data"""
        # For now, return None as director info is not in the CSV
        # This can be enhanced if director data is available in other columns
        return None
    
    def _clean_numeric_value(self, value: Any) -> Optional[float]:
        """Clean and convert numeric values"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        try:
            # Handle string numbers
            if isinstance(value, str):
                # Remove any non-numeric characters except decimal point
                cleaned = ''.join(c for c in value if c.isdigit() or c == '.')
                if cleaned:
                    return float(cleaned)
            else:
                return float(value)
        except (ValueError, TypeError):
            return None
            
        return None
    
    def _parse_row(self, row: pd.Series) -> Optional[MovieData]:
        """Parse a single CSV row into MovieData"""
        try:
            # Extract year from release_date if available
            year = None
            if 'release_date' in row and pd.notna(row['release_date']):
                try:
                    release_date = pd.to_datetime(row['release_date'])
                    year = release_date.year
                except:
                    pass
            
            # Create movie data dictionary
            movie_dict = {
                'title': row.get('title', '').strip() or row.get('original_title', '').strip(),
                'description': row.get('overview', '').strip() if pd.notna(row.get('overview')) else None,
                'year': year,
                'genre': self._extract_genres(row.get('genres', '')),
                'director': self._extract_director(row.get('production_companies', '')),
                'rating': self._clean_numeric_value(row.get('vote_average')),
                'duration': self._clean_numeric_value(row.get('runtime')),
                'release_date': row.get('release_date') if pd.notna(row.get('release_date')) else None,
                'poster_url': row.get('poster_path', '').strip() if pd.notna(row.get('poster_path')) else None,
                'imdb_id': row.get('imdb_id', '').strip() if pd.notna(row.get('imdb_id')) else None,
                'budget': self._clean_numeric_value(row.get('budget')),
                'revenue': self._clean_numeric_value(row.get('revenue')),
                'popularity': self._clean_numeric_value(row.get('popularity')),
                'vote_count': self._clean_numeric_value(row.get('vote_count'))
            }
            
            # Validate using Pydantic model
            return MovieData(**movie_dict)
            
        except Exception as e:
            logger.warning(f"Error parsing row: {e}")
            return None
    
    def validate_csv_format(self, file_path: Path) -> bool:
        """Validate CSV file format and required columns"""
        try:
            # Read just the header to check columns
            df_sample = pd.read_csv(file_path, nrows=0)
            
            # Check for required columns
            missing_columns = [col for col in self.required_columns if col not in df_sample.columns]
            if missing_columns:
                raise CSVParsingError(f"Missing required columns: {missing_columns}")
                
            return True
            
        except pd.errors.EmptyDataError:
            raise CSVParsingError("CSV file is empty")
        except pd.errors.ParserError as e:
            raise CSVParsingError(f"CSV parsing error: {e}")
        except Exception as e:
            raise CSVParsingError(f"Error validating CSV format: {e}")
    
    def parse_csv_batch(self, file_path: Path, skip_rows: int = 0) -> Generator[List[MovieData], None, None]:
        """Parse CSV file in batches and yield lists of MovieData objects"""
        try:
            # Validate file format first
            self.validate_csv_format(file_path)
            
            # Read CSV in chunks
            chunk_iter = pd.read_csv(
                file_path,
                chunksize=self.batch_size,
                skiprows=skip_rows,
                low_memory=False,
                dtype=str  # Read all columns as strings initially
            )
            
            total_processed = 0
            total_valid = 0
            
            for chunk_num, chunk in enumerate(chunk_iter):
                batch_movies = []
                
                for idx, row in chunk.iterrows():
                    total_processed += 1
                    movie_data = self._parse_row(row)
                    
                    if movie_data:
                        batch_movies.append(movie_data)
                        total_valid += 1
                
                logger.info(f"Processed batch {chunk_num + 1}: {len(batch_movies)} valid movies out of {len(chunk)} rows")
                
                if batch_movies:
                    yield batch_movies
            
            logger.info(f"CSV parsing complete. Total processed: {total_processed}, Valid: {total_valid}")
            
        except Exception as e:
            raise CSVParsingError(f"Error parsing CSV file: {e}")
    
    def parse_csv_file(self, file_path: Path) -> List[MovieData]:
        """Parse entire CSV file and return list of MovieData objects"""
        all_movies = []
        
        for batch in self.parse_csv_batch(file_path):
            all_movies.extend(batch)
        
        return all_movies
    
    def get_csv_stats(self, file_path: Path) -> Dict[str, Any]:
        """Get statistics about the CSV file"""
        try:
            df = pd.read_csv(file_path, low_memory=False)
            
            stats = {
                'total_rows': len(df),
                'columns': list(df.columns),
                'missing_titles': df['title'].isna().sum() if 'title' in df.columns else 0,
                'date_range': {
                    'earliest': None,
                    'latest': None
                },
                'rating_stats': {
                    'min': None,
                    'max': None,
                    'mean': None
                }
            }
            
            # Handle date range safely
            if 'release_date' in df.columns:
                try:
                    # Convert to datetime and handle errors
                    dates = pd.to_datetime(df['release_date'], errors='coerce')
                    valid_dates = dates.dropna()
                    if len(valid_dates) > 0:
                        stats['date_range']['earliest'] = str(valid_dates.min().date())
                        stats['date_range']['latest'] = str(valid_dates.max().date())
                except Exception:
                    pass
            
            # Handle rating stats safely
            if 'vote_average' in df.columns:
                try:
                    # Convert to numeric and handle errors
                    ratings = pd.to_numeric(df['vote_average'], errors='coerce')
                    valid_ratings = ratings.dropna()
                    if len(valid_ratings) > 0:
                        stats['rating_stats']['min'] = float(valid_ratings.min())
                        stats['rating_stats']['max'] = float(valid_ratings.max())
                        stats['rating_stats']['mean'] = float(valid_ratings.mean())
                except Exception:
                    pass
            
            return stats
            
        except Exception as e:
            raise CSVParsingError(f"Error getting CSV stats: {e}")


def create_sample_csv_data(output_path: Path) -> None:
    """Create sample CSV data for testing"""
    sample_data = [
        {
            'title': 'The Matrix',
            'original_title': 'The Matrix',
            'overview': 'A computer hacker learns from mysterious rebels about the true nature of his reality.',
            'genres': "[{'id': 28, 'name': 'Action'}, {'id': 878, 'name': 'Science Fiction'}]",
            'release_date': '1999-03-30',
            'vote_average': 8.2,
            'runtime': 136,
            'poster_path': '/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg',
            'imdb_id': 'tt0133093',
            'budget': 63000000,
            'revenue': 463517383,
            'popularity': 60.441,
            'vote_count': 18098
        },
        {
            'title': 'Inception',
            'original_title': 'Inception',
            'overview': 'Cobb, a skilled thief who commits corporate espionage by infiltrating the subconscious.',
            'genres': "[{'id': 28, 'name': 'Action'}, {'id': 878, 'name': 'Science Fiction'}, {'id': 53, 'name': 'Thriller'}]",
            'release_date': '2010-07-15',
            'vote_average': 8.4,
            'runtime': 148,
            'poster_path': '/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
            'imdb_id': 'tt1375666',
            'budget': 160000000,
            'revenue': 825532764,
            'popularity': 29.108,
            'vote_count': 31546
        },
        {
            'title': 'The Godfather',
            'original_title': 'The Godfather',
            'overview': 'The aging patriarch of an organized crime dynasty transfers control to his reluctant son.',
            'genres': "[{'id': 18, 'name': 'Drama'}, {'id': 80, 'name': 'Crime'}]",
            'release_date': '1972-03-14',
            'vote_average': 9.2,
            'runtime': 175,
            'poster_path': '/3bhkrj58Vtu7enYsRolD1fZdja1.jpg',
            'imdb_id': 'tt0068646',
            'budget': 6000000,
            'revenue': 245066411,
            'popularity': 41.109,
            'vote_count': 15283
        }
    ]
    
    df = pd.DataFrame(sample_data)
    df.to_csv(output_path, index=False)
    logger.info(f"Sample CSV data created at {output_path}")