from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), index=True, nullable=False)
    
    url = Column(String, nullable=False)
    title = Column(String, nullable=True)
    snippet = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    
    domain = Column(String, nullable=True)
    published_at = Column(String, nullable=True)
    
    relevance_score = Column(Float, default=0.0)
    status = Column(String, nullable=False, default="FETCHED") # FETCHED, FAILED, IGNORED
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    task = relationship("AgentTask")
