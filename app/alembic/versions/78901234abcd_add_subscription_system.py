# app/alembic/versions/78901234abcd_add_subscription_system.py
"""add subscription system tables

Revision ID: 78901234abcd
Revises: 67890123abcd
Create Date: 2025-06-03 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '78901234abcd'
down_revision: Union[str, None] = '67890123abcd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types first
    # op.execute("CREATE TYPE resetintervalenum AS ENUM ('one_time', 'monthly')")
    # op.execute("CREATE TYPE subscriptionstatus AS ENUM ('active', 'cancelled', 'expired', 'pending')")
    # op.execute("CREATE TYPE aicalltypeenum AS ENUM ('beat_generation', 'scene_description', 'scene_segment', 'shortening', 'rewriting', 'expansion', 'continuation')")

    # Create subscription_plans table
    op.create_table('subscription_plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('price', sa.DECIMAL(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('free_trial_calls', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reset_interval', sa.Enum('one_time', 'monthly', name='resetintervalenum', schema='public'), nullable=False),
        sa.Column('features', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_subscription_plans_id'), 'subscription_plans', ['id'], unique=False)

    # Create user_subscriptions table
    op.create_table('user_subscriptions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('plan_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.Enum('active', 'cancelled', 'expired', 'pending', name='subscriptionstatus', schema='public'), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_reference', sa.String(length=255), nullable=True),
        sa.Column('payment_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_subscriptions_id'), 'user_subscriptions', ['id'], unique=False)
    op.create_index('ix_user_subscriptions_user_id', 'user_subscriptions', ['user_id'], unique=False)

    # Create ai_usage_log table
    op.create_table('ai_usage_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('call_type', sa.Enum('beat_generation', 'scene_description', 'scene_segment', 'shortening', 'rewriting', 'expansion', 'continuation', name='aicalltypeenum', schema='public'), nullable=False),
        sa.Column('script_id', sa.UUID(), nullable=True),
        sa.Column('usuage_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['script_id'], ['scripts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_usage_log_id'), 'ai_usage_log', ['id'], unique=False)
    op.create_index('ix_ai_usage_log_user_id', 'ai_usage_log', ['user_id'], unique=False)
    op.create_index('ix_ai_usage_log_timestamp', 'ai_usage_log', ['timestamp'], unique=False)

    # Insert default subscription plans
    op.execute("""
        INSERT INTO subscription_plans (id, name, display_name, price, currency, duration_days, free_trial_calls, reset_interval, features)
        VALUES 
        (gen_random_uuid(), 'free', 'Free Plan', 0.00, 'INR', 0, 5, 'monthly', '{"ai_calls_per_month": 5, "scripts": 3, "export": false}'),
        (gen_random_uuid(), 'monthly', 'Monthly Pro', 399.00, 'INR', 30, 0, 'monthly', '{"ai_calls_per_month": "unlimited", "scripts": "unlimited", "export": true, "priority_support": false}'),
        (gen_random_uuid(), 'annual', 'Annual Pro', 3999.00, 'INR', 365, 0, 'monthly', '{"ai_calls_per_month": "unlimited", "scripts": "unlimited", "export": true, "priority_support": true, "discount": "17%"}')
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index(op.f('ix_ai_usage_log_timestamp'), table_name='ai_usage_log')
    op.drop_index(op.f('ix_ai_usage_log_user_id'), table_name='ai_usage_log')
    op.drop_index(op.f('ix_ai_usage_log_id'), table_name='ai_usage_log')
    op.drop_table('ai_usage_log')
    
    op.drop_index('ix_user_subscriptions_user_id', table_name='user_subscriptions')
    op.drop_index(op.f('ix_user_subscriptions_id'), table_name='user_subscriptions')
    op.drop_table('user_subscriptions')
    
    op.drop_index(op.f('ix_subscription_plans_id'), table_name='subscription_plans')
    op.drop_table('subscription_plans')
    
    # Drop ENUM types
    op.execute("DROP TYPE aicalltypeenum")
    op.execute("DROP TYPE subscriptionstatus")
    op.execute("DROP TYPE resetintervalenum")