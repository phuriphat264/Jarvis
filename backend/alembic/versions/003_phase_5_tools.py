"""phase_5_tools

Revision ID: 003_phase_5
Revises: 002_phase_4
Create Date: 2026-09-05 09:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_phase_5'
down_revision: Union[str, None] = '002_phase_4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('messages', sa.Column('tool_calls', sa.JSON(), nullable=True))
    op.add_column('messages', sa.Column('tool_call_id', sa.String(), nullable=True))
    op.add_column('messages', sa.Column('tool_name', sa.String(), nullable=True))
    
    # Create index for tool_call_id
    op.create_index(op.f('ix_messages_tool_call_id'), 'messages', ['tool_call_id'], unique=False)
    
    # Alter content to be nullable (since tool calls might have no text content)
    op.alter_column('messages', 'content', existing_type=sa.Text(), nullable=True)

def downgrade() -> None:
    # Revert content to not null
    # Note: If there are messages with null content, this will fail. We might need to fill them with '' first, but standard downgrade is this:
    op.execute("UPDATE messages SET content = '' WHERE content IS NULL")
    op.alter_column('messages', 'content', existing_type=sa.Text(), nullable=False)
    
    op.drop_index(op.f('ix_messages_tool_call_id'), table_name='messages')
    op.drop_column('messages', 'tool_name')
    op.drop_column('messages', 'tool_call_id')
    op.drop_column('messages', 'tool_calls')
