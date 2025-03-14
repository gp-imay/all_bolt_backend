"""add script creation method and progress tracking

Revision ID: c73a4ce38d14
Revises: 1b7252df88d6
Create Date: 2025-02-18 22:52:34.299838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = 'c73a4ce38d14'
down_revision: Union[str, None] = '1b7252df88d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first
    scriptcreationmethod = sa.Enum('FROM_SCRATCH', 'WITH_AI', 'UPLOAD', name='scriptcreationmethod')
    scriptcreationmethod.create(op.get_bind(), checkfirst=True)
    
    # Add column as nullable first
    op.add_column('scripts', sa.Column('creation_method', sa.Enum('FROM_SCRATCH', 'WITH_AI', 'UPLOAD', name='scriptcreationmethod'), nullable=True))
    
    # Update existing rows to have a default value
    scripts = table('scripts',
        column('creation_method', sa.Enum('FROM_SCRATCH', 'WITH_AI', 'UPLOAD', name='scriptcreationmethod'))
    )
    op.execute(scripts.update().values(creation_method='FROM_SCRATCH'))
    
    # Now alter the column to be non-nullable
    op.alter_column('scripts', 'creation_method', nullable=False)


def downgrade() -> None:
    # Drop the column
    op.drop_column('scripts', 'creation_method')
    
    # Drop the enum type
    op.execute('DROP TYPE scriptcreationmethod')