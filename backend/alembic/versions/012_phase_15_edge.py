"""phase 15 edge

Revision ID: 012
Revises: 011
Create Date: 2026-09-05 12:12:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '012'
down_revision: Union[str, None] = '011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # edge_nodes
    op.create_table('edge_nodes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('node_id', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('hardware_info', sa.JSON(), nullable=True),
    sa.Column('software_version', sa.String(), nullable=True),
    sa.Column('capabilities', sa.JSON(), nullable=True),
    sa.Column('auth_key', sa.String(), nullable=True),
    sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_edge_nodes_id'), 'edge_nodes', ['id'], unique=False)
    op.create_index(op.f('ix_edge_nodes_node_id'), 'edge_nodes', ['node_id'], unique=True)
    op.create_index(op.f('ix_edge_nodes_user_id'), 'edge_nodes', ['user_id'], unique=False)

    # edge_enrollments
    op.create_table('edge_enrollments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('enrollment_code', sa.String(), nullable=False),
    sa.Column('used', sa.Boolean(), nullable=True),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_edge_enrollments_enrollment_code'), 'edge_enrollments', ['enrollment_code'], unique=True)
    op.create_index(op.f('ix_edge_enrollments_id'), 'edge_enrollments', ['id'], unique=False)
    op.create_index(op.f('ix_edge_enrollments_user_id'), 'edge_enrollments', ['user_id'], unique=False)

    # edge_events
    op.create_table('edge_events',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('node_id', sa.String(), nullable=False),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['node_id'], ['edge_nodes.node_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_edge_events_id'), 'edge_events', ['id'], unique=False)
    op.create_index(op.f('ix_edge_events_node_id'), 'edge_events', ['node_id'], unique=False)

def downgrade() -> None:
    op.drop_table('edge_events')
    op.drop_table('edge_enrollments')
    op.drop_table('edge_nodes')
