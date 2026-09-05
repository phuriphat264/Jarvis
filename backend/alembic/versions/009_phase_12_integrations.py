"""phase 12 integrations

Revision ID: 009
Revises: 008
Create Date: 2026-09-05 11:51:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # integration_connections
    op.create_table('integration_connections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('provider', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('external_account_id', sa.String(), nullable=True),
    sa.Column('display_name', sa.String(), nullable=True),
    sa.Column('scopes', sa.String(), nullable=True),
    sa.Column('encrypted_access_token', sa.Text(), nullable=True),
    sa.Column('encrypted_refresh_token', sa.Text(), nullable=True),
    sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('metadata_json', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integration_connections_id'), 'integration_connections', ['id'], unique=False)
    op.create_index(op.f('ix_integration_connections_provider'), 'integration_connections', ['provider'], unique=False)
    op.create_index(op.f('ix_integration_connections_user_id'), 'integration_connections', ['user_id'], unique=False)

    # pending_actions
    op.create_table('pending_actions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('tool_name', sa.String(), nullable=False),
    sa.Column('arguments', sa.JSON(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pending_actions_id'), 'pending_actions', ['id'], unique=False)
    op.create_index(op.f('ix_pending_actions_user_id'), 'pending_actions', ['user_id'], unique=False)

    # notification_preferences
    op.create_table('notification_preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('in_app_enabled', sa.Boolean(), nullable=True),
    sa.Column('line_enabled', sa.Boolean(), nullable=True),
    sa.Column('telegram_enabled', sa.Boolean(), nullable=True),
    sa.Column('email_enabled', sa.Boolean(), nullable=True),
    sa.Column('quiet_hours_enabled', sa.Boolean(), nullable=True),
    sa.Column('quiet_hours_start', sa.String(), nullable=True),
    sa.Column('quiet_hours_end', sa.String(), nullable=True),
    sa.Column('daily_summary_enabled', sa.Boolean(), nullable=True),
    sa.Column('meeting_reminder_enabled', sa.Boolean(), nullable=True),
    sa.Column('task_overdue_enabled', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preferences_id'), 'notification_preferences', ['id'], unique=False)
    op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_notification_preferences_user_id'), table_name='notification_preferences')
    op.drop_index(op.f('ix_notification_preferences_id'), table_name='notification_preferences')
    op.drop_table('notification_preferences')
    op.drop_index(op.f('ix_pending_actions_user_id'), table_name='pending_actions')
    op.drop_index(op.f('ix_pending_actions_id'), table_name='pending_actions')
    op.drop_table('pending_actions')
    op.drop_index(op.f('ix_integration_connections_user_id'), table_name='integration_connections')
    op.drop_index(op.f('ix_integration_connections_provider'), table_name='integration_connections')
    op.drop_index(op.f('ix_integration_connections_id'), table_name='integration_connections')
    op.drop_table('integration_connections')
