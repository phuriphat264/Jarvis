from typing import Optional
from pydantic import BaseModel
import logging
from app.core.config import settings
import base64

logger = logging.getLogger("jarvis.stt")

class STTResult(BaseModel):
    text: str
    language: str
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None

class BaseSTTProvider:
    async def transcribe(self, audio_data: bytes, language: Optional[str] = None, context: Optional[str] = None) -> STTResult:
        raise NotImplementedError

class MockSTTProvider(BaseSTTProvider):
    async def transcribe(self, audio_data: bytes, language: Optional[str] = None, context: Optional[str] = None) -> STTResult:
        logger.info(f"MockSTTProvider transcribing {len(audio_data)} bytes...")
        return STTResult(
            text="ตอนนี้มีงานอะไรที่ต้องทำบ้าง",
            language=language or settings.STT_LANGUAGE,
            confidence=0.99,
            duration_seconds=4.2
        )

class OpenAISTTProvider(BaseSTTProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.model = "whisper-1"

    async def transcribe(self, audio_data: bytes, language: Optional[str] = None, context: Optional[str] = None) -> STTResult:
        import io
        import tempfile
        
        # Whisper API requires a file-like object with a name
        audio_file = io.BytesIO(audio_data)
        audio_file.name = "audio.mp3" # Fake filename to satisfy API
        
        kwargs = {
            "model": self.model,
            "file": audio_file
        }
        
        if language:
            kwargs["language"] = language
        elif settings.STT_LANGUAGE:
            kwargs["language"] = settings.STT_LANGUAGE
            
        if context:
            kwargs["prompt"] = context
            
        response = await self.client.audio.transcriptions.create(**kwargs)
        
        return STTResult(
            text=response.text,
            language=language or settings.STT_LANGUAGE,
            confidence=None,
            duration_seconds=None
        )

class STTProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseSTTProvider:
        name = provider_name or settings.STT_PROVIDER
        if name.lower() == "openai":
            return OpenAISTTProvider()
        return MockSTTProvider()
