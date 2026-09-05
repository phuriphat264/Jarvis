import uuid
import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.document import Document, DocumentChunk
from app.core.dependencies import get_current_user
from app.schemas.schemas import APIResponse
from app.core.config import settings
from app.core_service.rag.pipeline import DocumentPipeline
from app.core_service.rag.retriever import RAGRetriever

router = APIRouter()

ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".xlsx", ".csv", ".pptx", ".txt", ".md",
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp",
    ".h", ".hpp", ".cs", ".go", ".rs", ".php", ".html", ".css",
    ".scss", ".json", ".yaml", ".yml", ".xml", ".sql", ".sh",
    ".png", ".jpg", ".jpeg", ".webp"
}

@router.post("/upload", response_model=APIResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Validate extension
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file extension: {ext}")
        
    # Read file content
    content = await file.read()
    size_bytes = len(content)
    
    # Validate size
    if size_bytes > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB")
        
    # Validate total files
    result = await db.execute(select(func.count()).select_from(Document).where(Document.user_id == current_user.id))
    total_files = result.scalar() or 0
    if total_files >= settings.MAX_FILES_PER_USER:
        raise HTTPException(status_code=400, detail="Maximum number of files reached")
        
    # Calculate SHA256
    file_hash = hashlib.sha256(content).hexdigest()
    
    # Check for duplicate
    dup_result = await db.execute(select(Document).where(
        Document.user_id == current_user.id,
        Document.sha256 == file_hash
    ))
    dup_doc = dup_result.scalars().first()
    if dup_doc:
        return APIResponse(success=True, data={"id": dup_doc.id, "status": dup_doc.status, "message": "Duplicate file detected."})
        
    # Phase 9: Image Validation
    if ext in [".png", ".jpg", ".jpeg", ".webp"]:
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(content))
            width, height = img.size
            pixels = width * height
            
            if width > settings.MAX_IMAGE_WIDTH or height > settings.MAX_IMAGE_HEIGHT:
                raise HTTPException(status_code=400, detail=f"Image dimensions exceed limit ({settings.MAX_IMAGE_WIDTH}x{settings.MAX_IMAGE_HEIGHT})")
            if pixels > settings.MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=400, detail="Image pixel count exceeds limit")
                
            # Check for animation (reject)
            if getattr(img, "is_animated", False):
                raise HTTPException(status_code=400, detail="Animated images are not supported")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
    # Ensure storage dir
    os.makedirs(settings.FILE_STORAGE_PATH, exist_ok=True)
    user_dir = os.path.join(settings.FILE_STORAGE_PATH, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(user_dir, doc_id)
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
        
    # Create DB record
    doc = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        original_filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        extension=ext,
        size_bytes=size_bytes,
        sha256=file_hash,
        storage_path=file_path,
        status="PROCESSING"
    )
    db.add(doc)
    await db.commit()
    
    # Background processing
    pipeline = DocumentPipeline(db)
    background_tasks.add_task(pipeline.process_document, doc.id)
    
    return APIResponse(success=True, data={"id": doc.id, "status": "PROCESSING"})

@router.get("", response_model=APIResponse)
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    
    data = []
    for doc in docs:
        data.append({
            "id": doc.id,
            "filename": doc.original_filename,
            "status": doc.status,
            "size_bytes": doc.size_bytes,
            "created_at": doc.created_at.isoformat() if doc.created_at else None,
            "error_message": doc.error_message
        })
        
    return APIResponse(success=True, data={"files": data})

@router.delete("/{file_id}", response_model=APIResponse)
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == current_user.id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
        
    # Delete chunks (Cascade should handle this if configured, but let's be explicit)
    await db.execute(DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc.id))
    
    doc.status = "DELETED"
    
    # Remove physical file
    if os.path.exists(doc.storage_path):
        try:
            os.remove(doc.storage_path)
        except:
            pass
            
    await db.commit()
    
    return APIResponse(success=True, data={"status": "DELETED"})

@router.post("/{file_id}/reprocess", response_model=APIResponse)
async def reprocess_file(
    file_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == current_user.id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
        
    if doc.status == "DELETED":
        raise HTTPException(status_code=400, detail="Cannot reprocess deleted file")
        
    # Delete existing chunks
    await db.execute(DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc.id))
    
    doc.status = "PROCESSING"
    doc.error_message = None
    await db.commit()
    
    # Background processing
    pipeline = DocumentPipeline(db)
    background_tasks.add_task(pipeline.process_document, doc.id)
    
    return APIResponse(success=True, data={"id": doc.id, "status": "PROCESSING"})

from fastapi.responses import FileResponse

@router.get("/{file_id}/preview")
async def preview_file(
    file_id: str,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    from app.core.config import settings
    from jose import JWTError, jwt
    
    if not token:
        raise HTTPException(status_code=401, detail="Token required for preview")
        
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    result = await db.execute(select(Document).where(Document.id == file_id, Document.user_id == user_id))
    doc = result.scalars().first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="File not found")
        
    if doc.status == "DELETED":
        raise HTTPException(status_code=404, detail="File deleted")
        
    if doc.extension not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(status_code=400, detail="Only images can be previewed")
        
    if not os.path.exists(doc.storage_path):
        raise HTTPException(status_code=404, detail="File content not found")
        
    return FileResponse(doc.storage_path, media_type=doc.mime_type)
