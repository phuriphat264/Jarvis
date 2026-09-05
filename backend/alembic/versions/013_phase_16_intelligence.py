"""phase 16 intelligence

Revision ID: 013
Revises: 012
Create Date: 2026-09-05 12:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '013'
down_revision: Union[str, None] = '012'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # intelligence_settings
    op.create_table('intelligence_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('proactive_assistant_enabled', sa.Boolean(), nullable=True),
    sa.Column('proactive_voice_enabled', sa.Boolean(), nullable=True),
    sa.Column('routine_suggestions_enabled', sa.Boolean(), nullable=True),
    sa.Column('smart_daily_briefing_enabled', sa.Boolean(), nullable=True),
    sa.Column('deadline_warnings_enabled', sa.Boolean(), nullable=True),
    sa.Column('iot_suggestions_enabled', sa.Boolean(), nullable=True),
    sa.Column('environment_suggestions_enabled', sa.Boolean(), nullable=True),
    sa.Column('auto_low_risk_actions', sa.Boolean(), nullable=True),
    sa.Column('quiet_hours_start', sa.String(), nullable=True),
    sa.Column('quiet_hours_end', sa.String(), nullable=True),
    sa.Column('max_notifications_per_day', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_intelligence_settings_id'), 'intelligence_settings', ['id'], unique=False)
    op.create_index(op.f('ix_intelligence_settings_user_id'), 'intelligence_settings', ['user_id'], unique=True)

    # routines
    op.create_table('routines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('trigger_type', sa.String(), nullable=False),
    sa.Column('conditions', sa.JSON(), nullable=False),
    sa.Column('actions', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('source', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_routines_id'), 'routines', ['id'], unique=False)
    op.create_index(op.f('ix_routines_user_id'), 'routines', ['user_id'], unique=False)

    # proactive_recommendations
    op.create_table('proactive_recommendations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('message', sa.String(), nullable=False),
    sa.Column('reason', sa.JSON(), nullable=True),
    sa.Column('priority', sa.String(), nullable=True),
    sa.Column('action_level', sa.String(), nullable=True),
    sa.Column('fingerprint', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_proactive_recommendations_id'), 'proactive_recommendations', ['id'], unique=False)
    op.create_index(op.f('ix_proactive_recommendations_user_id'), 'proactive_recommendations', ['user_id'], unique=False)

    # recommendation_feedback
    op.create_table('recommendation_feedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recommendation_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('feedback_type', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['recommendation_id'], ['proactive_recommendations.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendation_feedback_id'), 'recommendation_feedback', ['id'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_recommendation_id'), 'recommendation_feedback', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_recommendation_feedback_user_id'), 'recommendation_feedback', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('recommendation_feedback')
    op.drop_table('proactive_recommendations')
    op.drop_table('routines')
    op.drop_table('intelligence_settings')
