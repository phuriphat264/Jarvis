"""phase_4_memory

Revision ID: 002_phase_4
Revises: 001_phase_3
Create Date: 2026-09-04 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '002_phase_4'
down_revision: Union[str, None] = '001_phase_3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    op.create_table('memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(), nullable=False),
        sa.Column('importance', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('source_type', sa.String(), nullable=True, server_default='conversation'),
        sa.Column('source_conversation_id', sa.Integer(), nullable=True),
        sa.Column('source_message_id', sa.Integer(), nullable=True),
        sa.Column('embedding', Vector(dim=1536), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)
    op.create_index(op.f('ix_memories_user_id'), 'memories', ['user_id'], unique=False)
    op.create_index(op.f('ix_memories_memory_type'), 'memories', ['memory_type'], unique=False)
    op.create_index(op.f('ix_memories_status'), 'memories', ['status'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_memories_status'), table_name='memories')
    op.drop_index(op.f('ix_memories_memory_type'), table_name='memories')
    op.drop_index(op.f('ix_memories_user_id'), table_name='memories')
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
