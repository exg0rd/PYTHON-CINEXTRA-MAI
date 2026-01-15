"""Add search indexes for movies

Revision ID: 0bdaaa2f66ee
Revises: f3bc8af23853
Create Date: 2026-01-11 23:35:41.264870

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0bdaaa2f66ee'
down_revision: Union[str, None] = 'f3bc8af23853'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add regular indexes for SQLite (no full-text search support in basic SQLite)
    # We'll implement search using LIKE queries with these indexes
    op.create_index('idx_movies_title', 'movies', ['title'])
    op.create_index('idx_movies_genre', 'movies', ['genre'])
    op.create_index('idx_movies_director', 'movies', ['director'])
    
    # Add composite indexes for sorting performance
    op.create_index('idx_movies_year_rating', 'movies', ['year', 'rating'])
    op.create_index('idx_movies_rating_year', 'movies', ['rating', 'year'])
    
    # Add index for review count sorting (will be used in joins)
    op.create_index('idx_reviews_movie_count', 'reviews', ['movie_id'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_reviews_movie_count', 'reviews')
    op.drop_index('idx_movies_rating_year', 'movies')
    op.drop_index('idx_movies_year_rating', 'movies')
    op.drop_index('idx_movies_director', 'movies')
    op.drop_index('idx_movies_genre', 'movies')
    op.drop_index('idx_movies_title', 'movies')
