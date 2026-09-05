import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from app.core.config import settings
from app.database.models.message import Message

logger = logging.getLogger("jarvis.memory_extractor")

class ExtractedMemory(BaseModel):
    content: str
    memory_type: str
    importance: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)

class ExtractionResult(BaseModel):
    memories: List[ExtractedMemory]

class BaseMemoryExtractor:
    async def extract(self, messages: List[Message]) -> ExtractionResult:
        raise NotImplementedError

class MockMemoryExtractor(BaseMemoryExtractor):
    async def extract(self, messages: List[Message]) -> ExtractionResult:
        # Mock logic: if we see "remember" or "จำ", extract something
        extracted = []
        for msg in messages:
            if msg.role == 'user' and ("remember" in msg.content.lower() or "จำ" in msg.content):
                extracted.append(ExtractedMemory(
                    content=f"Mock memory from: {msg.content[:20]}",
                    memory_type="preference",
                    importance=0.8,
                    confidence=0.9
                ))
        return ExtractionResult(memories=extracted)

class LLMMemoryExtractor(BaseMemoryExtractor):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        # It's better to use a cheaper/faster model for extraction if possible, but we'll use OPENAI_MODEL
        self.model = settings.OPENAI_MODEL
        
        self.system_prompt = """
You are an advanced memory extraction system. Analyze the following conversation and extract long-term memories about the user.
Extract facts, preferences, projects, goals, or instructions.
Only extract information that is explicitly stated or strongly implied by the user. Do NOT hallucinate.
Do not extract transient information (like "I ate lunch").
Output JSON matching this schema:
{
  "memories": [
    {
      "content": "A concise, factual statement about the user.",
      "memory_type": "preference | project | goal | fact | instruction",
      "importance": 0.0 to 1.0,
      "confidence": 0.0 to 1.0
    }
  ]
}
Return ONLY valid JSON.
"""

    async def extract(self, messages: List[Message]) -> ExtractionResult:
        if not messages:
            return ExtractionResult(memories=[])
            
        # Format messages for the prompt
        chat_text = "\n".join([f"{m.role}: {m.content}" for m in messages])
        
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": chat_text}
                ],
                response_format={ "type": "json_object" },
                temperature=0.0
            )
            
            result_text = response.choices[0].message.content
            data = json.loads(result_text)
            return ExtractionResult(**data)
        except Exception as e:
            logger.error(f"Failed to extract memory via LLM: {str(e)}")
            return ExtractionResult(memories=[])

class MemoryExtractorFactory:
    @staticmethod
    def get_extractor(provider_name: str = None) -> BaseMemoryExtractor:
        name = provider_name or settings.AI_PROVIDER
        if name.lower() == "openai":
            return LLMMemoryExtractor()
        return MockMemoryExtractor()
