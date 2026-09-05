from fastapi import APIRouter, Depends, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.activity_log import ActivityLog
from app.schemas.schemas import MemoryCreate, MemoryUpdate, MemoryResponse
from app.core.dependencies import get_current_user
from app.services.memory_service import MemoryService
from app.services.memory_search_service import MemorySearchService
from app.interfaces.embedding_provider import EmbeddingProviderFactory

router = APIRouter()
embedder = EmbeddingProviderFactory.get_provider()
searcher = MemorySearchService()

@router.get("/", response_model=List[MemoryResponse])
async def get_memories(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await MemoryService.get_memories(db, current_user.id)

@router.post("/", response_model=MemoryResponse)
async def create_memory(mem_in: MemoryCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    embedding = await embedder.embed(mem_in.content)
    mem = await MemoryService.create_memory(
        db, 
        current_user.id, 
        mem_in.content, 
        mem_in.memory_type, 
        embedding, 
        mem_in.importance, 
        mem_in.confidence, 
        source_type="manual"
    )
    
    log = ActivityLog(user_id=current_user.id, action="MEMORY_CREATED_MANUALLY", details={"memory_id": mem.id})
    db.add(log)
    await db.commit()
    return mem

@router.get("/search", response_model=List[MemoryResponse])
async def search_memories(q: str = Query(...), current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Standard threshold or slightly lower for manual search
    return await searcher.search(db, current_user.id, q, top_k=10, threshold=0.5)

@router.patch("/{memory_id}", response_model=MemoryResponse)
async def update_memory(memory_id: int, mem_in: MemoryUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    updates = mem_in.dict(exclude_unset=True)
    if "content" in updates:
        # Re-embed
        updates["embedding"] = await embedder.embed(updates["content"])
        
    mem = await MemoryService.update_memory(db, memory_id, current_user.id, updates)
    
    log = ActivityLog(user_id=current_user.id, action="MEMORY_UPDATED", details={"memory_id": mem.id})
    db.add(log)
    await db.commit()
    return mem

@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await MemoryService.delete_memory(db, memory_id, current_user.id)
    
    log = ActivityLog(user_id=current_user.id, action="MEMORY_DELETED", details={"memory_id": memory_id})
    db.add(log)
    await db.commit()
    return {"success": True}
