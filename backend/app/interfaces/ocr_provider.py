from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import base64
from app.core.config import settings

class OCRBlock(BaseModel):
    text: str
    confidence: Optional[float] = None
    bbox: Optional[Dict[str, float]] = None

class OCRResult(BaseModel):
    text: str
    blocks: List[OCRBlock]
    confidence: Optional[float] = None

class BaseOCRProvider:
    async def extract_text(self, image_data: bytes, mime_type: str = "image/png") -> OCRResult:
        raise NotImplementedError

class MockOCRProvider(BaseOCRProvider):
    async def extract_text(self, image_data: bytes, mime_type: str = "image/png") -> OCRResult:
        return OCRResult(
            text="Mock OCR Text. Total: 48,500 THB",
            blocks=[
                OCRBlock(text="Mock OCR Text.", confidence=0.99, bbox={"x": 10, "y": 10, "w": 100, "h": 20}),
                OCRBlock(text="Total: 48,500 THB", confidence=0.98, bbox={"x": 10, "y": 30, "w": 100, "h": 20})
            ],
            confidence=0.98
        )

class OpenAIOCRProvider(BaseOCRProvider):
    def __init__(self):
        import openai
        self.client = openai.AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.model = settings.OPENAI_MODEL
        
    async def extract_text(self, image_data: bytes, mime_type: str = "image/png") -> OCRResult:
        b64_image = base64.b64encode(image_data).decode("utf-8")
        prompt = "Extract all text from this image exactly as written. If it's a table, preserve the tabular structure as much as possible using markdown formatting or spacing."
        
        # In reality, gpt-4o does not easily provide bounding boxes without complex prompting,
        # but we will just return the full text for this implementation, and mock the bbox.
        messages = [
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
            max_tokens=2000
        )
        
        extracted_text = response.choices[0].message.content or ""
        
        return OCRResult(
            text=extracted_text,
            blocks=[OCRBlock(text=extracted_text, confidence=1.0)],
            confidence=1.0
        )

class OCRProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseOCRProvider:
        name = provider_name or settings.OCR_PROVIDER
        if name.lower() == "openai":
            return OpenAIOCRProvider()
        return MockOCRProvider()
