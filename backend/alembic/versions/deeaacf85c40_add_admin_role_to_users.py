"""Add admin role to users

Revision ID: deeaacf85c40
Revises: 0bdaaa2f66ee
Create Date: 2026-01-11 23:42:37.435266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deeaacf85c40'
down_revision: Union[str, None] = '0bdaaa2f66ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column to users table
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_admin column from users table
    op.drop_column('users', 'is_admin')
