from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True) # UUID string
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    extension = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String, index=True, nullable=True)
    storage_path = Column(String, nullable=False)
    
    status = Column(String, index=True, default="UPLOADED") 
    # UPLOADED, PROCESSING, READY, FAILED, NEEDS_OCR, DELETED
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, index=True) # UUID string
    document_id = Column(String, ForeignKey("documents.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    
    # 1536 is standard for OpenAI text-embedding-3-small
    embedding = Column(Vector(1536))
    
    # Structural metadata preservation
    page_number = Column(Integer, nullable=True)
    section_name = Column(String, nullable=True)
    sheet_name = Column(String, nullable=True)
    slide_number = Column(Integer, nullable=True)
    row_start = Column(Integer, nullable=True)
    row_end = Column(Integer, nullable=True)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    
    # Phase 9: Vision & OCR
    source_type = Column(String, default="NATIVE", index=True) # NATIVE, OCR
    bbox = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    block_index = Column(Integer, nullable=True)
    
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")
