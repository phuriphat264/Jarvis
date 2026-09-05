from typing import Optional
from pydantic import BaseModel
import logging
from app.core.config import settings

logger = logging.getLogger("jarvis.tts")

class TTSResult(BaseModel):
    audio_data: bytes
    mime_type: str
    duration_seconds: Optional[float] = None

class BaseTTSProvider:
    async def synthesize(self, text: str, voice: Optional[str] = None, language: Optional[str] = None, speed: Optional[float] = None) -> TTSResult:
        raise NotImplementedError

class MockTTSProvider(BaseTTSProvider):
    async def synthesize(self, text: str, voice: Optional[str] = None, language: Optional[str] = None, speed: Optional[float] = None) -> TTSResult:
        logger.info(f"MockTTSProvider synthesizing: {text}")
        
        # Create a small dummy valid WAV file or empty MP3
        # For simplicity, returning a tiny valid MP3 or silent data
        # Actually returning a valid 1-byte file might break some players, 
        # so let's just return a placeholder. Frontend should handle gracefully.
        
        # Dummy minimal mp3 data
        dummy_mp3 = b'ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf58.76.100\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xfb\x90\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        return TTSResult(
            audio_data=dummy_mp3,
            mime_type="audio/mpeg",
            duration_seconds=1.0
        )

class OpenAITTSProvider(BaseTTSProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.model = "tts-1"

    async def synthesize(self, text: str, voice: Optional[str] = None, language: Optional[str] = None, speed: Optional[float] = None) -> TTSResult:
        kwargs = {
            "model": self.model,
            "input": text,
            "voice": voice or settings.TTS_VOICE or "alloy",
            "speed": speed or settings.TTS_SPEED or 1.0,
            "response_format": "mp3"
        }
        
        response = await self.client.audio.speech.create(**kwargs)
        
        return TTSResult(
            audio_data=response.content,
            mime_type="audio/mpeg",
            duration_seconds=None
        )

class TTSProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseTTSProvider:
        name = provider_name or settings.TTS_PROVIDER
        if name.lower() == "openai":
            return OpenAITTSProvider()
        return MockTTSProvider()
