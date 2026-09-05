from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from fastapi import HTTPException
from app.database.models.conversation import Conversation
from app.database.models.message import Message

class ConversationService:
    @staticmethod
    async def get_or_create_conversation(db: AsyncSession, user_id: int, title: Optional[str] = None) -> Conversation:
        if not title:
            title = "New Conversation"
        conv = Conversation(user_id=user_id, title=title)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        return conv
        
    @staticmethod
    async def verify_ownership(db: AsyncSession, conversation_id: int, user_id: int) -> Conversation:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id, Conversation.status != "deleted"))
        conv = result.scalars().first()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found or access forbidden")
        return conv

    @staticmethod
    async def check_idempotency(db: AsyncSession, client_request_id: str) -> Optional[Message]:
        if not client_request_id:
            return None
        result = await db.execute(select(Message).where(Message.client_request_id == client_request_id))
        return result.scalars().first()

    @staticmethod
    async def add_message(db: AsyncSession, conversation_id: int, role: str, content: Optional[str] = None, client_request_id: str = None, tool_calls: list = None, tool_call_id: str = None, tool_name: str = None) -> Message:
        # Get max sequence
        result = await db.execute(select(func.max(Message.sequence)).where(Message.conversation_id == conversation_id))
        max_seq = result.scalar() or 0
        
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            client_request_id=client_request_id,
            sequence=max_seq + 1,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            tool_name=tool_name
        )
        db.add(msg)
        
        # update conversation timestamp
        conv = await db.get(Conversation, conversation_id)
        if conv:
            conv.last_message_at = func.now()
            
        await db.commit()
        await db.refresh(msg)
        logger.info(f"MESSAGE_ADDED: conv={conversation_id} role={role} seq={msg.sequence}")
        return msg

    @staticmethod
    async def get_messages(db: AsyncSession, conversation_id: int, limit: int = 50, before_sequence: Optional[int] = None) -> Tuple[List[Message], bool, Optional[int]]:
        query = select(Message).where(Message.conversation_id == conversation_id)
        
        if before_sequence is not None:
            query = query.where(Message.sequence < before_sequence)
            
        # Get descending for pagination, then reverse
        query = query.order_by(desc(Message.sequence)).limit(limit + 1)
        result = await db.execute(query)
        messages = result.scalars().all()
        
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:-1]
            
        next_cursor = messages[-1].sequence if messages else None
        
        # Reverse to return in chronological order
        messages.reverse()
        
        return messages, has_more, next_cursor
