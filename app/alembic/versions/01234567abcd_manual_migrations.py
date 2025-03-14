"""Create initial database schema

Revision ID: 01234567abcd
Revises: 
Create Date: 2025-03-14 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '01234567abcd'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types first
    # op.execute("CREATE TYPE public.actenum AS ENUM ('act_1', 'act_2a', 'act_2b', 'act_3')")
    # op.execute("CREATE TYPE public.beatsheettype AS ENUM ('BLAKE_SNYDER', 'HERO_JOURNEY', 'STORY_CIRCLE', 'PIXAR_STRUCTURE', 'TV_BEAT_SHEET', 'MINI_MOVIE', 'INDIE_FILM')")
    # op.execute("CREATE TYPE public.componenttype AS ENUM ('HEADING', 'ACTION', 'DIALOGUE', 'TRANSITION', 'CHARACTER')")
    # op.execute("CREATE TYPE public.scenegenerationstatus AS ENUM ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED')")
    # op.execute("CREATE TYPE public.scriptcreationmethod AS ENUM ('FROM_SCRATCH', 'WITH_AI', 'UPLOAD')")

    # Create users table
    op.create_table('users',
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('email_verified', sa.Boolean(), nullable=True),
        sa.Column('phone_verified', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_anonymous', sa.Boolean(), nullable=True),
        sa.Column('auth_role', sa.String(), nullable=True),
        sa.Column('auth_provider', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sign_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('app_metadata', sa.JSON(), nullable=True),
        sa.Column('user_metadata', sa.JSON(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('supabase_uid', sa.String(), nullable=False),
        sa.Column('is_super_user', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    # Create master_beat_sheets table
    op.create_table('master_beat_sheets',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('beat_sheet_type', sa.Enum('BLAKE_SNYDER', 'HERO_JOURNEY', 'STORY_CIRCLE', 'PIXAR_STRUCTURE', 'TV_BEAT_SHEET', 'MINI_MOVIE', 'INDIE_FILM', name='beatsheettype', schema='public'), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('number_of_beats', sa.Integer(), nullable=False),
        sa.Column('template', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('beat_sheet_type')
    )
    op.create_index('ix_master_beat_sheets_id', 'master_beat_sheets', ['id'], unique=False)

    # Create scripts table
    op.create_table('scripts',
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subtitle', sa.String(length=255), nullable=True),
        sa.Column('genre', sa.String(length=100), nullable=False),
        sa.Column('story', sa.Text(), nullable=False),
        sa.Column('is_file_uploaded', sa.Boolean(), nullable=False),
        sa.Column('file_url', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('script_progress', sa.Integer(), nullable=True),
        sa.Column('creation_method', sa.Enum('FROM_SCRATCH', 'WITH_AI', 'UPLOAD', name='scriptcreationmethod', schema='public'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scripts_id', 'scripts', ['id'], unique=False)
    op.create_index('ix_scripts_title', 'scripts', ['title'], unique=False)

    # Create beats table
    op.create_table('beats',
        sa.Column('script_id', sa.UUID(), nullable=False),
        sa.Column('master_beat_sheet_id', sa.UUID(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('beat_title', sa.String(length=1000), nullable=False),
        sa.Column('beat_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('beat_act', sa.Enum('act_1', 'act_2a', 'act_2b', 'act_3', name='actenum', schema='public'), nullable=False),
        sa.Column('complete_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['master_beat_sheet_id'], ['master_beat_sheets.id'], ),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('script_id', 'beat_title', name='unique_beat_title_per_script'),
        sa.UniqueConstraint('script_id', 'position', name='unique_position_per_script')
    )
    op.create_index('ix_beats_id', 'beats', ['id'], unique=False)

    # Create scene_description_beats table
    op.create_table('scene_description_beats',
        sa.Column('beat_id', sa.UUID(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('scene_heading', sa.String(length=1000), nullable=False),
        sa.Column('scene_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['beat_id'], ['beats.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scene_description_beats_id', 'scene_description_beats', ['id'], unique=False)

    # Create scene_segments table
    op.create_table('scene_segments',
        sa.Column('script_id', sa.UUID(), nullable=False),
        sa.Column('beat_id', sa.UUID(), nullable=True),
        sa.Column('scene_description_id', sa.UUID(), nullable=True),
        sa.Column('segment_number', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['beat_id'], ['beats.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['scene_description_id'], ['scene_description_beats.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scene_segments_id', 'scene_segments', ['id'], unique=False)

    # Create scene_segment_components table
    op.create_table('scene_segment_components',
        sa.Column('scene_segment_id', sa.UUID(), nullable=False),
        sa.Column('component_type', sa.Enum('HEADING', 'ACTION', 'DIALOGUE', 'TRANSITION', 'CHARACTER', name='componenttype', schema='public'), nullable=False),
        sa.Column('position', sa.Float(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('character_name', sa.String(length=255), nullable=True),
        sa.Column('parenthetical', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['scene_segment_id'], ['scene_segments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scene_segment_components_id', 'scene_segment_components', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('scene_segment_components')
    op.drop_table('scene_segments')
    op.drop_table('scene_description_beats')
    op.drop_table('beats')
    op.drop_table('scripts')
    op.drop_table('master_beat_sheets')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute("DROP TYPE public.scriptcreationmethod")
    op.execute("DROP TYPE public.scenegenerationstatus")
    op.execute("DROP TYPE public.componenttype")
    op.execute("DROP TYPE public.beatsheettype")
    op.execute("DROP TYPE public.actenum")