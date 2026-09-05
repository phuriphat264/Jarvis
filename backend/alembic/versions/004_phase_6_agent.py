"""phase_6_agent

Revision ID: 004_phase_6
Revises: 003_phase_5
Create Date: 2026-09-05 10:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_phase_6'
down_revision: Union[str, None] = '003_phase_5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agent_tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=True),
        sa.Column('request_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('current_step', sa.Integer(), nullable=True),
        sa.Column('max_steps', sa.Integer(), nullable=True),
        sa.Column('final_result', sa.Text(), nullable=True),
        sa.Column('error', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tasks_id'), 'agent_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_request_id'), 'agent_tasks', ['request_id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_user_id'), 'agent_tasks', ['user_id'], unique=False)

    # Create agent_steps table
    op.create_table(
        'agent_steps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('tool_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('duration_ms', sa.Float(), nullable=True),
        sa.Column('error', sa.JSON(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['agent_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_steps_id'), 'agent_steps', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_steps_id'), table_name='agent_steps')
    op.drop_table('agent_steps')
    op.drop_index(op.f('ix_agent_tasks_user_id'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_request_id'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_id'), table_name='agent_tasks')
    op.drop_table('agent_tasks')
