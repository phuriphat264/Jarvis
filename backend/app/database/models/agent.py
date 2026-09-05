from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    request_id = Column(String, index=True, nullable=True)
    
    # Phase 13 Extensions
    agent_manager_run_id = Column(Integer, ForeignKey("agent_manager_runs.id"), nullable=True)
    agent_name = Column(String, nullable=True)
    parent_step_id = Column(String, nullable=True)
    
    status = Column(String, nullable=False, default="PENDING") 
    # PENDING, RUNNING, WAITING_CONFIRMATION, COMPLETED, FAILED, CANCELLED, TIMEOUT, LIMIT_REACHED
    
    current_step = Column(Integer, default=0)
    max_steps = Column(Integer, default=6)
    
    final_result = Column(Text, nullable=True)
    error = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steps = relationship("AgentStep", back_populates="task", cascade="all, delete-orphan")


class AgentStep(Base):
    __tablename__ = "agent_steps"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=False)
    
    step_number = Column(Integer, nullable=False)
    action_type = Column(String, nullable=False) # THINK, TOOL_CALL, TOOL_RESULT, FINAL_ANSWER
    tool_name = Column(String, nullable=True)
    status = Column(String, nullable=False, default="COMPLETED") # PENDING, COMPLETED, FAILED, CANCELLED
    
    duration_ms = Column(Float, nullable=True)
    error = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    task = relationship("AgentTask", back_populates="steps")
