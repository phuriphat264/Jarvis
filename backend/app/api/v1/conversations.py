from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from app.database.session import get_db
from app.database.models.user import User
from app.database.models.conversation import Conversation
from app.database.models.message import Message
from app.database.models.activity_log import ActivityLog
from app.schemas.schemas import ConversationCreate, ConversationUpdate, ConversationResponse, MessageCreate, MessageResponse, MessagePairResponse, PaginatedMessagesResponse
from app.core.dependencies import get_current_user
from app.core_service.jarvis import JarvisCore
from app.services.conversation_service import ConversationService

router = APIRouter()
jarvis = JarvisCore()

@router.post("/", response_model=ConversationResponse)
async def create_conversation(conv_in: ConversationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await ConversationService.get_or_create_conversation(db, current_user.id, conv_in.title)
    
    log = ActivityLog(user_id=current_user.id, action="CONVERSATION_CREATED", details={"conversation_id": conv.id})
    db.add(log)
    await db.commit()
    
    return conv

@router.get("/", response_model=List[ConversationResponse])
async def get_conversations(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # exclude deleted
    result = await db.execute(select(Conversation).where(Conversation.user_id == current_user.id, Conversation.status != "deleted").order_by(desc(Conversation.updated_at)))
    return result.scalars().all()

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return await ConversationService.verify_ownership(db, conversation_id, current_user.id)

@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, conv_in: ConversationUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await ConversationService.verify_ownership(db, conversation_id, current_user.id)
    
    if conv_in.title is not None:
        conv.title = conv_in.title
        log = ActivityLog(user_id=current_user.id, action="CONVERSATION_RENAMED", details={"conversation_id": conv.id, "title": conv.title})
        db.add(log)
    if conv_in.status is not None:
        conv.status = conv_in.status
        log = ActivityLog(user_id=current_user.id, action=f"CONVERSATION_STATUS_CHANGED_{conv.status.upper()}", details={"conversation_id": conv.id})
        db.add(log)
        
    await db.commit()
    await db.refresh(conv)
    return conv

@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    conv = await ConversationService.verify_ownership(db, conversation_id, current_user.id)
    conv.status = "deleted"
    
    log = ActivityLog(user_id=current_user.id, action="CONVERSATION_DELETED", details={"conversation_id": conv.id})
    db.add(log)
    await db.commit()
    return {"success": True}

@router.post("/{conversation_id}/messages", response_model=MessagePairResponse)
async def create_message(
    conversation_id: int, 
    msg_in: MessageCreate, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    conv = await ConversationService.verify_ownership(db, conversation_id, current_user.id)
        
    # Idempotency check
    if msg_in.client_request_id:
        existing = await ConversationService.check_idempotency(db, msg_in.client_request_id)
        if existing:
            raise HTTPException(status_code=400, detail="Duplicate request id")
            
    # Save user message
    user_msg = await ConversationService.add_message(db, conversation_id, "user", msg_in.content, msg_in.client_request_id)
    
    # Load history for context
    history_result = await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence))
    history = history_result.scalars().all()
    
    # Process via JARVIS Core
    new_messages = await jarvis.process(
        msg_in.content, 
        history, 
        db, 
        current_user.id, 
        background_tasks, 
        conversation_id, 
        msg_in.client_request_id,
        msg_in.document_id
    )
    
    # Save assistant and tool messages
    saved_messages = []
    for nm in new_messages:
        msg = await ConversationService.add_message(
            db=db,
            conversation_id=conversation_id,
            role=nm["role"],
            content=nm.get("content"),
            tool_calls=nm.get("tool_calls"),
            tool_call_id=nm.get("tool_call_id"),
            tool_name=nm.get("name")
        )
        saved_messages.append(msg)
        
    # Find the final assistant message to return in the pair response
    final_ai_msg = saved_messages[-1] if saved_messages else None
    
    # Log activity
    log = ActivityLog(user_id=current_user.id, action="AI_REQUEST_COMPLETED", details={"conversation_id": conversation_id})
    db.add(log)
    await db.commit()
    
    return {
        "success": True,
        "data": {
            "user_message": {
                "id": user_msg.id,
                "conversation_id": user_msg.conversation_id,
                "role": user_msg.role,
                "content": user_msg.content,
                "sequence": user_msg.sequence,
                "created_at": user_msg.created_at,
                "client_request_id": user_msg.client_request_id
            },
            "assistant_message": {
                "id": final_ai_msg.id if final_ai_msg else None,
                "conversation_id": final_ai_msg.conversation_id if final_ai_msg else conversation_id,
                "role": final_ai_msg.role if final_ai_msg else "assistant",
                "content": final_ai_msg.content if final_ai_msg else "",
                "sequence": final_ai_msg.sequence if final_ai_msg else 0,
                "created_at": final_ai_msg.created_at if final_ai_msg else None,
                "client_request_id": None
            }
        }
    }

@router.get("/{conversation_id}/messages", response_model=PaginatedMessagesResponse)
async def get_messages(
    conversation_id: int, 
    limit: int = Query(50, le=100), 
    before: Optional[int] = None,
    current_user: User = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    await ConversationService.verify_ownership(db, conversation_id, current_user.id)
    messages, has_more, next_cursor = await ConversationService.get_messages(db, conversation_id, limit, before)
    
    return {
        "data": messages,
        "has_more": has_more,
        "next_cursor": next_cursor
    }
