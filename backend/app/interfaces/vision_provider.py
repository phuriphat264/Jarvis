from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import base64
from app.core.config import settings

class VisionResult(BaseModel):
    description: str
    observations: List[str] = []
    extracted_text: Optional[str] = None
    structured_data: Dict[str, Any] = {}
    confidence: Optional[float] = None

class BaseVisionProvider:
    async def analyze_image(self, image_data: bytes, prompt: str, mime_type: str = "image/png") -> VisionResult:
        raise NotImplementedError

class MockVisionProvider(BaseVisionProvider):
    async def analyze_image(self, image_data: bytes, prompt: str, mime_type: str = "image/png") -> VisionResult:
        return VisionResult(
            description="Mock vision description. The image shows a sample invoice.",
            observations=["Invoice number is INV-001", "Total amount is 48,500 THB"],
            extracted_text="Invoice INV-001\nTotal: 48,500 THB",
            confidence=0.99
        )

class OpenAIVisionProvider(BaseVisionProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
    async def analyze_image(self, image_data: bytes, prompt: str, mime_type: str = "image/png") -> VisionResult:
        b64_image = base64.b64encode(image_data).decode("utf-8")
        
        system_prompt = "You are a visual analysis AI. Answer the user's question about the image accurately."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_image}"
                        }
                    }
                ]
            }
        ]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content or ""
        
        return VisionResult(
            description=content,
            observations=[],
            extracted_text=None,
            confidence=1.0
        )

class VisionProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseVisionProvider:
        name = provider_name or settings.VISION_PROVIDER
        if name.lower() == "openai":
            return OpenAIVisionProvider()
        return MockVisionProvider()
