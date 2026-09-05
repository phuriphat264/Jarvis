from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Auth & User ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Conversation & Message ---
class MessageCreate(BaseModel):
    content: str
    client_request_id: Optional[str] = None
    document_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: Optional[str] = None
    sequence: int
    created_at: datetime
    client_request_id: Optional[str] = None
    
    # Tool fields
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None

    class Config:
        from_attributes = True

class MessagePairResponse(BaseModel):
    success: bool
    data: dict # Will contain user_message and assistant_message

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PaginatedMessagesResponse(BaseModel):
    data: List[MessageResponse]
    has_more: bool
    next_cursor: Optional[int] = None

# --- Memory ---
class MemoryCreate(BaseModel):
    content: str
    memory_type: str
    importance: float = 0.5
    confidence: float = 1.0

class MemoryUpdate(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[str] = None
    importance: Optional[float] = None
    confidence: Optional[float] = None
    status: Optional[str] = None

class MemoryResponse(BaseModel):
    id: int
    user_id: int
    content: str
    memory_type: str
    importance: float
    confidence: float
    source_type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[dict] = None
