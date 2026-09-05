import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models.message import Message
from app.interfaces.memory_extractor import MemoryExtractorFactory
from app.interfaces.embedding_provider import EmbeddingProviderFactory
from app.services.memory_service import MemoryService
from app.services.memory_search_service import MemorySearchService
from app.core.config import settings
from app.database.session import SessionLocal

logger = logging.getLogger("jarvis.memory_extraction")

class MemoryExtractionService:
    def __init__(self):
        self.extractor = MemoryExtractorFactory.get_extractor()
        self.embedder = EmbeddingProviderFactory.get_provider()
        self.searcher = MemorySearchService()

    async def run_extraction_background(self, user_id: int, conversation_id: int, recent_messages: List[Message]):
        if not settings.MEMORY_ENABLED:
            return
            
        try:
            logger.info(f"MEMORY_EXTRACTION_STARTED for user={user_id}, conv={conversation_id}")
            extraction_result = await self.extractor.extract(recent_messages)
            
            if not extraction_result.memories:
                return

            # Open a new DB session since this runs in the background
            async with SessionLocal() as db:
                for extracted_mem in extraction_result.memories:
                    if extracted_mem.confidence < settings.MEMORY_MIN_CONFIDENCE:
                        continue
                    if extracted_mem.importance < settings.MEMORY_MIN_IMPORTANCE:
                        continue

                    # 1. Embed the candidate
                    embedding = await self.embedder.embed(extracted_mem.content)
                    
                    # 2. Check for duplicates/conflicts (similarity > 0.85 means very similar concept)
                    similar = await self.searcher.search_similar(db, user_id, embedding, threshold=0.85)
                    
                    if similar:
                        # Found existing memory. We could update or just skip. 
                        # For Phase 4, we skip if highly similar to prevent duplicate spam.
                        logger.info(f"Skipping duplicate memory for user={user_id}: {extracted_mem.content}")
                        continue
                        
                    # 3. Create memory
                    await MemoryService.create_memory(
                        db=db,
                        user_id=user_id,
                        content=extracted_mem.content,
                        memory_type=extracted_mem.memory_type,
                        embedding=embedding,
                        importance=extracted_mem.importance,
                        confidence=extracted_mem.confidence,
                        source_type="conversation",
                        source_conversation_id=conversation_id,
                        source_message_id=recent_messages[-1].id if recent_messages else None
                    )
                    
            logger.info(f"MEMORY_EXTRACTION_COMPLETED for user={user_id}")
            
        except Exception as e:
            logger.error(f"MEMORY_EXTRACTION_FAILED: {str(e)}")
