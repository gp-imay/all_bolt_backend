"""adding beat act to beats column

Revision ID: 9996f32986ae
Revises: 3541aa926db2
Create Date: 2025-02-20 02:21:44.877049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


# revision identifiers, used by Alembic.
revision: str = '9996f32986ae'
down_revision: Union[str, None] = '3541aa926db2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum type first if it doesn't exist
    actenum = sa.Enum('act_1', 'act_2', 'act_3', name='actenum')
    actenum.create(op.get_bind(), checkfirst=True)
    
    # Add column as nullable first
    op.add_column('beats', sa.Column('beat_act', sa.Enum('act_1', 'act_2', 'act_3', name='actenum'), nullable=True))
    
    # Update existing rows with a default value
    beats = table('beats',
        column('beat_act', sa.Enum('act_1', 'act_2', 'act_3', name='actenum'))
    )
    op.execute(beats.update().values(beat_act='act_1'))
    
    # Now alter the column to be non-nullable
    op.alter_column('beats', 'beat_act', nullable=False)


def downgrade() -> None:
    # Drop the column
    op.drop_column('beats', 'beat_act')
    
    # We don't drop the enum type in this downgrade because it might be used by other columns
    # If you're certain it's not used elsewhere, you can add:
    # op.execute('DROP TYPE actenum')