"""phase_9_vision

Revision ID: 007
Revises: 006
Create Date: 2026-09-05 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('document_chunks', sa.Column('source_type', sa.String(), server_default='NATIVE', nullable=True))
    op.add_column('document_chunks', sa.Column('bbox', sa.JSON(), nullable=True))
    op.add_column('document_chunks', sa.Column('confidence', sa.Float(), nullable=True))
    op.add_column('document_chunks', sa.Column('block_index', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_document_chunks_source_type'), 'document_chunks', ['source_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_document_chunks_source_type'), table_name='document_chunks')
    op.drop_column('document_chunks', 'block_index')
    op.drop_column('document_chunks', 'confidence')
    op.drop_column('document_chunks', 'bbox')
    op.drop_column('document_chunks', 'source_type')
