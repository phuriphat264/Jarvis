import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.session import get_db
from app.database.models.user import User
from app.database.models.message import Message
from app.database.models.activity_log import ActivityLog
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.schemas.schemas import APIResponse

from app.interfaces.stt_provider import STTProviderFactory
from app.interfaces.tts_provider import TTSProviderFactory
from app.services.conversation_service import ConversationService
from app.core_service.jarvis import JarvisCore

router = APIRouter()
logger = logging.getLogger("jarvis.voice")
jarvis = JarvisCore()

ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
ALLOWED_AUDIO_MIMES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/webm", "audio/ogg", "audio/flac", "audio/x-m4a"}

@router.post("/message")
async def process_voice_message(
    background_tasks: BackgroundTasks,
    conversation_id: int = Form(...),
    audio: UploadFile = File(...),
    document_id: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    1. Upload Audio
    2. Validate
    3. STT
    4. JARVIS Core
    5. TTS
    6. Return Audio URL / Base64 & Transcript
    """
    # Verify ownership
    conv = await ConversationService.verify_ownership(db, conversation_id, current_user.id)
    
    # Validate extension
    _, ext = os.path.splitext(audio.filename)
    ext = ext.lower()
    
    # Some browsers send blob without extension
    if ext and ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported audio extension")
        
    # Read audio
    audio_data = await audio.read()
    size_bytes = len(audio_data)
    
    if size_bytes > settings.MAX_AUDIO_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Audio exceeds maximum size of {settings.MAX_AUDIO_SIZE_MB}MB")
        
    if size_bytes == 0:
        raise HTTPException(status_code=400, detail="Empty audio file")

    logger.info(f"VOICE_SESSION_STARTED: user {current_user.id}, conv {conversation_id}")
    
    # Store audio physically if configured
    if settings.STORE_VOICE_AUDIO:
        try:
            storage_path = os.path.join(settings.FILE_STORAGE_PATH, "voice", str(current_user.id))
            os.makedirs(storage_path, exist_ok=True)
            file_path = os.path.join(storage_path, f"{uuid.uuid4()}{ext or '.webm'}")
            with open(file_path, "wb") as f:
                f.write(audio_data)
        except Exception as e:
            logger.warning(f"Failed to store voice audio: {e}")

    try:
        # 1. STT
        logger.info("VOICE_TRANSCRIPTION_STARTED")
        stt_provider = STTProviderFactory.get_provider()
        stt_result = await stt_provider.transcribe(audio_data)
        transcript = stt_result.text.strip()
        logger.info("VOICE_TRANSCRIPTION_COMPLETED")
        
        if not transcript:
            raise HTTPException(status_code=400, detail="Could not understand audio / Empty transcript")
            
        # 2. Add message to conversation (input_type="voice" via metadata if added)
        # We didn't migrate metadata on message, so we just add standard message
        user_msg = await ConversationService.add_message(db, conversation_id, "user", transcript)
        
        # Load history
        history_result = await db.execute(select(Message).where(Message.conversation_id == conversation_id).order_by(Message.sequence))
        history = history_result.scalars().all()
        
        # 3. JARVIS Core
        new_messages = await jarvis.process(
            transcript, 
            history, 
            db, 
            current_user.id, 
            background_tasks, 
            conversation_id, 
            None,
            document_id
        )
        
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
            
        final_ai_msg = saved_messages[-1] if saved_messages else None
        final_response_text = final_ai_msg.content if final_ai_msg else ""
        
        # 4. TTS
        tts_result = None
        audio_b64 = None
        if final_response_text:
            logger.info("VOICE_RESPONSE_STARTED")
            tts_provider = TTSProviderFactory.get_provider()
            tts_result = await tts_provider.synthesize(final_response_text)
            import base64
            audio_b64 = base64.b64encode(tts_result.audio_data).decode("utf-8")
            logger.info("VOICE_RESPONSE_COMPLETED")
            
        await db.commit()
        
        return {
            "success": True,
            "data": {
                "transcript": transcript,
                "response": final_response_text,
                "audio": {
                    "base64": audio_b64,
                    "mime_type": tts_result.mime_type if tts_result else None
                }
            }
        }
        
    except Exception as e:
        logger.error(f"VOICE_TRANSCRIPTION_FAILED or PROCESS_FAILED: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Voice processing failed: {str(e)}")
