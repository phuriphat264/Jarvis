import logging
from typing import List, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.database.models.memory import Memory

logger = logging.getLogger("jarvis.memory_service")

class MemoryService:
    @staticmethod
    async def get_memories(db: AsyncSession, user_id: int) -> List[Memory]:
        result = await db.execute(
            select(Memory)
            .where(Memory.user_id == user_id, Memory.status == "active")
            .order_by(desc(Memory.created_at))
        )
        return result.scalars().all()

    @staticmethod
    async def get_memory(db: AsyncSession, memory_id: int, user_id: int) -> Memory:
        result = await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == user_id, Memory.status != "deleted"))
        mem = result.scalars().first()
        if not mem:
            raise HTTPException(status_code=404, detail="Memory not found")
        return mem

    @staticmethod
    async def create_memory(
        db: AsyncSession, 
        user_id: int, 
        content: str, 
        memory_type: str, 
        embedding: List[float],
        importance: float = 0.5,
        confidence: float = 1.0,
        source_type: str = "manual",
        source_conversation_id: Optional[int] = None,
        source_message_id: Optional[int] = None
    ) -> Memory:
        mem = Memory(
            user_id=user_id,
            content=content,
            memory_type=memory_type,
            embedding=embedding,
            importance=importance,
            confidence=confidence,
            source_type=source_type,
            source_conversation_id=source_conversation_id,
            source_message_id=source_message_id
        )
        db.add(mem)
        await db.commit()
        await db.refresh(mem)
        logger.info(f"MEMORY_CREATED: id={mem.id} for user={user_id}")
        return mem

    @staticmethod
    async def update_memory(db: AsyncSession, memory_id: int, user_id: int, updates: dict) -> Memory:
        mem = await MemoryService.get_memory(db, memory_id, user_id)
        for k, v in updates.items():
            if hasattr(mem, k) and v is not None:
                setattr(mem, k, v)
        await db.commit()
        await db.refresh(mem)
        logger.info(f"MEMORY_UPDATED: id={mem.id} for user={user_id}")
        return mem

    @staticmethod
    async def delete_memory(db: AsyncSession, memory_id: int, user_id: int):
        mem = await MemoryService.get_memory(db, memory_id, user_id)
        mem.status = "deleted"
        await db.commit()
        logger.info(f"MEMORY_DELETED: id={mem.id} for user={user_id}")
