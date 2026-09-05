"""phase 13 agent manager

Revision ID: 010
Revises: 009
Create Date: 2026-09-05 11:58:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create agent_manager_runs table
    op.create_table('agent_manager_runs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('conversation_id', sa.Integer(), nullable=True),
    sa.Column('request_id', sa.String(), nullable=True),
    sa.Column('input_text', sa.Text(), nullable=False),
    sa.Column('route_type', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('plan', sa.JSON(), nullable=True),
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
    op.create_index(op.f('ix_agent_manager_runs_conversation_id'), 'agent_manager_runs', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_agent_manager_runs_id'), 'agent_manager_runs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_manager_runs_request_id'), 'agent_manager_runs', ['request_id'], unique=False)
    op.create_index(op.f('ix_agent_manager_runs_user_id'), 'agent_manager_runs', ['user_id'], unique=False)

    # Add columns to agent_tasks
    op.add_column('agent_tasks', sa.Column('agent_manager_run_id', sa.Integer(), nullable=True))
    op.add_column('agent_tasks', sa.Column('agent_name', sa.String(), nullable=True))
    op.add_column('agent_tasks', sa.Column('parent_step_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'agent_tasks', 'agent_manager_runs', ['agent_manager_run_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint(None, 'agent_tasks', type_='foreignkey')
    op.drop_column('agent_tasks', 'parent_step_id')
    op.drop_column('agent_tasks', 'agent_name')
    op.drop_column('agent_tasks', 'agent_manager_run_id')
    op.drop_index(op.f('ix_agent_manager_runs_user_id'), table_name='agent_manager_runs')
    op.drop_index(op.f('ix_agent_manager_runs_request_id'), table_name='agent_manager_runs')
    op.drop_index(op.f('ix_agent_manager_runs_id'), table_name='agent_manager_runs')
    op.drop_index(op.f('ix_agent_manager_runs_conversation_id'), table_name='agent_manager_runs')
    op.drop_table('agent_manager_runs')
