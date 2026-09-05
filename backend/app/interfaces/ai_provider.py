import json
import openai
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.core.config import settings

logger = logging.getLogger("jarvis.ai_provider")

class AIResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class BaseAIProvider:
    async def generate(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        raise NotImplementedError
        
    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AIResponse:
        raise NotImplementedError

class MockAIProvider(BaseAIProvider):
    async def generate(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        return "JARVIS AI Core is running in MOCK mode."
        
    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AIResponse:
        return AIResponse(content="Mock mode with tools.", tool_calls=None)

class OpenAIProvider(BaseAIProvider):
    def __init__(self):
        if not settings.AI_API_KEY:
            logger.warning("OpenAI API Key is not set.")
        self.client = openai.AsyncOpenAI(api_key=settings.AI_API_KEY, timeout=settings.AI_TIMEOUT)
        
    async def generate(self, messages: List[Dict[str, Any]], **kwargs) -> str:
        model = kwargs.get("model", settings.OPENAI_MODEL)
        temperature = kwargs.get("temperature", settings.AI_TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", settings.AI_MAX_TOKENS)
        
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content or ""

    async def generate_with_tools(self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs) -> AIResponse:
        model = kwargs.get("model", settings.OPENAI_MODEL)
        temperature = kwargs.get("temperature", settings.AI_TEMPERATURE)
        max_tokens = kwargs.get("max_tokens", settings.AI_MAX_TOKENS)
        
        create_kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if tools and settings.TOOLS_ENABLED:
            create_kwargs["tools"] = tools
            create_kwargs["tool_choice"] = "auto"

        response = await self.client.chat.completions.create(**create_kwargs)
        
        choice = response.choices[0].message
        content = choice.content
        
        tool_calls_out = None
        if choice.tool_calls:
            tool_calls_out = []
            for tc in choice.tool_calls:
                tool_calls_out.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments # JSON string
                    }
                })
                
        return AIResponse(content=content, tool_calls=tool_calls_out)

class AIProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseAIProvider:
        name = provider_name or settings.AI_PROVIDER
        if name.lower() == "openai":
            return OpenAIProvider()
        else:
            return MockAIProvider()
