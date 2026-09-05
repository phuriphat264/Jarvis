"""phase 14 iot

Revision ID: 011
Revises: 010
Create Date: 2026-09-05 12:05:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # iot_devices
    op.create_table('iot_devices',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('room', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('capabilities', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('gateway', sa.String(), nullable=True),
    sa.Column('topic_config', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iot_devices_id'), 'iot_devices', ['id'], unique=False)
    op.create_index(op.f('ix_iot_devices_user_id'), 'iot_devices', ['user_id'], unique=False)

    # iot_device_states
    op.create_table('iot_device_states',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('online', sa.Boolean(), nullable=True),
    sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
    sa.Column('power', sa.Boolean(), nullable=True),
    sa.Column('brightness', sa.Integer(), nullable=True),
    sa.Column('temperature', sa.Integer(), nullable=True),
    sa.Column('humidity', sa.Integer(), nullable=True),
    sa.Column('motion', sa.Boolean(), nullable=True),
    sa.Column('raw_state', sa.JSON(), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['iot_devices.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('device_id')
    )
    op.create_index(op.f('ix_iot_device_states_id'), 'iot_device_states', ['id'], unique=False)

    # iot_device_events
    op.create_table('iot_device_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('device_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('action', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('metadata', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['device_id'], ['iot_devices.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iot_device_events_id'), 'iot_device_events', ['id'], unique=False)
    op.create_index(op.f('ix_iot_device_events_user_id'), 'iot_device_events', ['user_id'], unique=False)

    # iot_device_groups
    op.create_table('iot_device_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iot_device_groups_id'), 'iot_device_groups', ['id'], unique=False)
    op.create_index(op.f('ix_iot_device_groups_user_id'), 'iot_device_groups', ['user_id'], unique=False)

    # iot_automations
    op.create_table('iot_automations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('enabled', sa.Boolean(), nullable=True),
    sa.Column('conditions', sa.JSON(), nullable=False),
    sa.Column('actions', sa.JSON(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_iot_automations_id'), 'iot_automations', ['id'], unique=False)
    op.create_index(op.f('ix_iot_automations_user_id'), 'iot_automations', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_table('iot_automations')
    op.drop_table('iot_device_groups')
    op.drop_table('iot_device_events')
    op.drop_table('iot_device_states')
    op.drop_table('iot_devices')
