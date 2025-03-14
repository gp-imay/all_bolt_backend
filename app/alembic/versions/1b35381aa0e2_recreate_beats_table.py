"""recreate_beats_table

Revision ID: 1b35381aa0e2
Revises: 2035ec976c9c
Create Date: 2025-02-20 03:02:17.915723

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = '1b35381aa0e2'
down_revision: Union[str, None] = '2035ec976c9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Skip table creation since it already exists
    # Just create the index if it doesn't exist
    try:
        op.create_index(op.f('ix_beats_id'), 'beats', ['id'], unique=False)
    except Exception:
        # Index might already exist, so we can ignore this error
        pass
    
    # Add any other necessary changes here if needed
    # For example, if you need to add new columns or alter existing ones


def downgrade() -> None:
    # Modify downgrade operation to only drop the index
    try:
        op.drop_index(op.f('ix_beats_id'), table_name='beats')
    except Exception:
        # Index might not exist, so we can ignore this error
        pass
    
    # Do not drop the table in downgrade since we're no longer creating it in upgrade