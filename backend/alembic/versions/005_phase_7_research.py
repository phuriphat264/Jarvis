"""phase_7_research

Revision ID: 005_phase_7
Revises: 004_phase_6
Create Date: 2026-09-05 10:24:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_phase_7'
down_revision: Union[str, None] = '004_phase_6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create research_sources table
    op.create_table(
        'research_sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('published_at', sa.String(), nullable=True),
        sa.Column('relevance_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['agent_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_sources_id'), 'research_sources', ['id'], unique=False)
    op.create_index(op.f('ix_research_sources_task_id'), 'research_sources', ['task_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_research_sources_task_id'), table_name='research_sources')
    op.drop_index(op.f('ix_research_sources_id'), table_name='research_sources')
    op.drop_table('research_sources')
