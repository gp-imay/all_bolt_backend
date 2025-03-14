"""adding character to scene segment enums

Revision ID: a0b1ffd03659
Revises: ee91ea496743
Create Date: 2025-03-04 02:32:08.368659

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = 'a0b1ffd03659'
down_revision: Union[str, None] = 'ee91ea496743'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if the enum type exists
    conn = op.get_bind()
    result = conn.execute(text(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'componenttype')"
    )).scalar()
    
    if not result:
        # If the enum doesn't exist, create it with all values including the new one
        enum = ENUM("HEADING", "ACTION", "DIALOGUE", "TRANSITION", "CHARACTER", 
                    name="componenttype", create_type=True)
        enum.create(op.get_bind(), checkfirst=True)
    else:
        # If the enum exists, try to add the new value
        try:
            op.execute("ALTER TYPE componenttype ADD VALUE 'CHARACTER'")
        except Exception as e:
            # Value might already exist, which is fine
            print(f"Note: {str(e)}")
            pass


def downgrade() -> None:
    # Unfortunately, PostgreSQL doesn't support removing values from enum types directly
    # The best we can do is note that this happened
    print("Note: Cannot remove values from PostgreSQL enum types. The CHARACTER value will remain.")
    # We are not implementing the complex enum recreation as it might cause data loss