from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.models.document import DocumentChunk, Document
from app.interfaces.embedding_provider import EmbeddingProviderFactory
from app.core.config import settings

class RAGRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedder = EmbeddingProviderFactory.get_provider()
        
    async def search(self, user_id: int, query: str, document_id: Optional[str] = None, top_k: int = None) -> List[Dict[str, Any]]:
        top_k = top_k or settings.RAG_TOP_K
        threshold = settings.RAG_SIMILARITY_THRESHOLD
        
        query_embedding = await self.embedder.embed(query)
        
        # Use pgvector cosine distance: embedding.cosine_distance(query_embedding)
        # Cosine similarity is 1 - distance
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        similarity = 1.0 - distance
        
        stmt = select(DocumentChunk, Document, similarity.label("similarity")).join(
            Document, DocumentChunk.document_id == Document.id
        ).where(
            DocumentChunk.user_id == user_id,
            Document.status == "READY",
            similarity >= threshold
        )
        
        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
            
        stmt = stmt.order_by(distance).limit(top_k)
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        output = []
        for chunk, doc, sim in rows:
            output.append({
                "chunk_id": chunk.id,
                "document_id": doc.id,
                "filename": doc.original_filename,
                "text": chunk.text,
                "similarity": float(sim),
                "page_number": chunk.page_number,
                "sheet_name": chunk.sheet_name,
                "slide_number": chunk.slide_number,
                "row_start": chunk.row_start,
                "row_end": chunk.row_end,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "source_type": getattr(chunk, "source_type", "NATIVE"),
                "bbox": getattr(chunk, "bbox", None),
                "confidence": getattr(chunk, "confidence", None),
                "block_index": getattr(chunk, "block_index", None)
            })
            
        return output
