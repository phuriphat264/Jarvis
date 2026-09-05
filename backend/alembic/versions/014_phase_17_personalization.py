"""phase 17 personalization

Revision ID: 014
Revises: 013
Create Date: 2026-09-05 12:29:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '014'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_preferences
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('scope_id', sa.String(), nullable=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_user_preferences_id', 'user_preferences', ['id'], unique=False)
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'], unique=False)

    # preference_candidates
    op.create_table(
        'preference_candidates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('evidence_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_preference_candidates_id', 'preference_candidates', ['id'], unique=False)
    op.create_index('ix_preference_candidates_user_id', 'preference_candidates', ['user_id'], unique=False)

    # behavior_events
    op.create_table(
        'behavior_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('context', sa.String(), nullable=True),
        sa.Column('entity_type', sa.String(), nullable=True),
        sa.Column('entity_id', sa.String(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_behavior_events_id', 'behavior_events', ['id'], unique=False)
    op.create_index('ix_behavior_events_user_id', 'behavior_events', ['user_id'], unique=False)

    # personalization_feedback
    op.create_table(
        'personalization_feedback',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preference_id', sa.Integer(), nullable=True),
        sa.Column('feedback_type', sa.String(), nullable=False),
        sa.Column('context', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['preference_id'], ['user_preferences.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_personalization_feedback_id', 'personalization_feedback', ['id'], unique=False)
    op.create_index('ix_personalization_feedback_user_id', 'personalization_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('personalization_feedback')
    op.drop_table('behavior_events')
    op.drop_table('preference_candidates')
    op.drop_table('user_preferences')
