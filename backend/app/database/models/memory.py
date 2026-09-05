from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.database.base import Base

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    content = Column(Text, nullable=False)
    memory_type = Column(String, index=True, nullable=False) # e.g., 'preference', 'project', 'fact'
    importance = Column(Float, default=0.5)
    confidence = Column(Float, default=1.0)
    
    source_type = Column(String, default="conversation") # 'conversation', 'manual', 'system'
    source_conversation_id = Column(Integer, nullable=True)
    source_message_id = Column(Integer, nullable=True)
    
    # Ensure correct dimension for text-embedding-3-small which is 1536
    embedding = Column(Vector(1536))
    
    status = Column(String, default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
