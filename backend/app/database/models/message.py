from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String, nullable=False) # 'user', 'assistant', 'system', 'tool'
    content = Column(Text, nullable=True) # Can be null if it only has tool_calls
    client_request_id = Column(String, index=True, nullable=True)
    sequence = Column(Integer, index=True, default=0)
    
    # Tool specific fields
    tool_calls = Column(JSON, nullable=True) # Stores the raw tool calls from LLM
    tool_call_id = Column(String, index=True, nullable=True) # Link a 'tool' role message to a call
    tool_name = Column(String, nullable=True) # Name of the tool executed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
