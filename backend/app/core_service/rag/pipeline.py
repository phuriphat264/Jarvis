import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import func
from app.database.models.document import Document, DocumentChunk
from app.core_service.rag.parsers import registry as parser_registry
from app.core_service.rag.chunker import StructureAwareChunker
from app.interfaces.embedding_provider import EmbeddingProviderFactory

logger = logging.getLogger("jarvis.rag.pipeline")

class DocumentPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunker = StructureAwareChunker()
        self.embedder = EmbeddingProviderFactory.get_provider()
        
    async def process_document(self, document_id: str):
        # 1. Fetch doc
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalars().first()
        
        if not doc or doc.status != "PROCESSING":
            return
            
        try:
            # 2. Parse
            parser = parser_registry.get_parser(doc.mime_type, doc.extension)
            if not parser:
                raise ValueError(f"No parser found for {doc.mime_type} / {doc.extension}")
                
            content = await parser.parse(doc.storage_path, doc.id)
            if not content.elements:
                doc.status = "NEEDS_OCR"
                doc.error_message = "No text could be extracted."
                await self.db.commit()
                return
                
            # 3. Chunk
            chunks_data = self.chunker.chunk(content)
            
            # 4. Embed & Store
            # For performance in a real app, this should be batched. We do sequentially for simplicity.
            for i, chunk_dict in enumerate(chunks_data):
                text = chunk_dict["text"]
                if not text:
                    continue
                    
                embedding_vector = await self.embedder.embed(text)
                
                # Fetch Phase 9 properties from chunk_dict if present, or assume NATIVE
                # Chunker needs to pass them through. Assuming they are passed or defaults.
                source_type = chunk_dict.get("source_type", "NATIVE")
                confidence = chunk_dict.get("confidence")
                bbox = chunk_dict.get("bbox")
                block_index = chunk_dict.get("block_index")
                
                chunk_record = DocumentChunk(
                    id=str(uuid.uuid4()),
                    document_id=doc.id,
                    user_id=doc.user_id,
                    chunk_index=i,
                    text=text,
                    embedding=embedding_vector,
                    page_number=chunk_dict.get("page_number"),
                    sheet_name=chunk_dict.get("sheet_name"),
                    slide_number=chunk_dict.get("slide_number"),
                    row_start=chunk_dict.get("row_start"),
                    row_end=chunk_dict.get("row_end"),
                    line_start=chunk_dict.get("line_start"),
                    line_end=chunk_dict.get("line_end"),
                    source_type=source_type,
                    confidence=confidence,
                    bbox=bbox,
                    block_index=block_index
                )
                self.db.add(chunk_record)
                
            doc.status = "READY"
            doc.processed_at = func.now()
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            await self.db.rollback()
            
            # Refetch to update status since rollback cleared the instance state
            result = await self.db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalars().first()
            if doc:
                doc.status = "FAILED"
                doc.error_message = str(e)
                doc.processed_at = func.now()
                await self.db.commit()
