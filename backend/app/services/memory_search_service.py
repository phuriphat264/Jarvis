import logging
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
from app.database.models.memory import Memory
from app.interfaces.embedding_provider import EmbeddingProviderFactory
from app.core.config import settings

logger = logging.getLogger("jarvis.memory_search")

class MemorySearchService:
    def __init__(self):
        self.embedder = EmbeddingProviderFactory.get_provider()
        
    async def search(self, db: AsyncSession, user_id: int, query: str, top_k: int = None, threshold: float = None) -> List[Memory]:
        if not settings.MEMORY_ENABLED:
            return []
            
        top_k = top_k or settings.MEMORY_TOP_K
        threshold = threshold or settings.MEMORY_SIMILARITY_THRESHOLD
        
        try:
            query_embedding = await self.embedder.embed(query)
            
            # Use pgvector cosine distance: embedding <=> vector
            # Cosine distance = 1 - cosine similarity. So similarity = 1 - distance.
            # We want similarity >= threshold, which means distance <= 1 - threshold
            max_distance = 1.0 - threshold
            
            stmt = select(Memory).where(
                Memory.user_id == user_id,
                Memory.status == "active",
                Memory.embedding.cosine_distance(query_embedding) <= max_distance
            ).order_by(
                Memory.embedding.cosine_distance(query_embedding)
            ).limit(top_k)
            
            result = await db.execute(stmt)
            memories = result.scalars().all()
            
            logger.info(f"MEMORY_SEARCH: Found {len(memories)} relevant memories for user={user_id}")
            return memories
            
        except Exception as e:
            logger.error(f"MEMORY_SEARCH_FAILED: {str(e)}")
            return [] # Fail gracefully so chat continues

    async def search_similar(self, db: AsyncSession, user_id: int, embedding: List[float], threshold: float = 0.90) -> List[Memory]:
        """Used for deduplication/conflict resolution before adding a new memory."""
        try:
            max_distance = 1.0 - threshold
            stmt = select(Memory).where(
                Memory.user_id == user_id,
                Memory.status == "active",
                Memory.embedding.cosine_distance(embedding) <= max_distance
            ).order_by(
                Memory.embedding.cosine_distance(embedding)
            ).limit(1)
            
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"SIMILAR_MEMORY_SEARCH_FAILED: {str(e)}")
            return []
