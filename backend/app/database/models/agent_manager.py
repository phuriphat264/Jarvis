from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class AgentManagerRun(Base):
    __tablename__ = "agent_manager_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    request_id = Column(String, index=True, nullable=True)
    
    input_text = Column(Text, nullable=False)
    route_type = Column(String, nullable=False) # e.g. MULTI_AGENT, PERSONAL_OS
    
    status = Column(String, nullable=False, default="PENDING") 
    # PENDING, PLANNING, RUNNING, COMPLETED, FAILED, CANCELLED, TIMEOUT, LIMIT_REACHED
    
    plan = Column(JSON, nullable=True)
    final_result = Column(Text, nullable=True)
    error = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Note: Steps are related to AgentTask by adding agent_manager_run_id to AgentTask
