"""Add video streaming fields to movies table

Revision ID: add_video_streaming_fields
Revises: 
Create Date: 2024-01-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_video_streaming_fields'
down_revision = None
depends_on = None


def upgrade() -> None:
    # Add video streaming fields to movies table
    op.add_column('movies', sa.Column('video_file_id', sa.String(255), nullable=True))
    op.add_column('movies', sa.Column('processing_status', sa.String(50), nullable=True, default='pending'))
    op.add_column('movies', sa.Column('available_qualities', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('hls_manifest_url', sa.String(500), nullable=True))
    op.add_column('movies', sa.Column('duration_seconds', sa.Integer(), nullable=True))
    op.add_column('movies', sa.Column('subtitles', sa.JSON(), nullable=True))
    op.add_column('movies', sa.Column('audio_tracks', sa.JSON(), nullable=True))
    
    # Create indexes for better performance
    op.create_index('idx_movies_video_file_id', 'movies', ['video_file_id'])
    op.create_index('idx_movies_processing_status', 'movies', ['processing_status'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_movies_processing_status', table_name='movies')
    op.drop_index('idx_movies_video_file_id', table_name='movies')
    
    # Remove columns
    op.drop_column('movies', 'audio_tracks')
    op.drop_column('movies', 'subtitles')
    op.drop_column('movies', 'duration_seconds')
    op.drop_column('movies', 'hls_manifest_url')
    op.drop_column('movies', 'available_qualities')
    op.drop_column('movies', 'processing_status')
    op.drop_column('movies', 'video_file_id')