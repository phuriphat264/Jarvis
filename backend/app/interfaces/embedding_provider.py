from typing import List
from openai import AsyncOpenAI
from app.core.config import settings

class BaseEmbeddingProvider:
    async def embed(self, text: str) -> List[float]:
        raise NotImplementedError

class MockEmbeddingProvider(BaseEmbeddingProvider):
    async def embed(self, text: str) -> List[float]:
        # Return a dummy vector of the correct dimension (1536)
        # We can make it pseudo-random based on text length to allow basic distance testing
        val = len(text) / 100.0
        return [val] * 1536

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.EMBEDDING_MODEL

    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            input=[text],
            model=self.model
        )
        return response.data[0].embedding

class EmbeddingProviderFactory:
    @staticmethod
    def get_provider(provider_name: str = None) -> BaseEmbeddingProvider:
        name = provider_name or settings.EMBEDDING_PROVIDER
        if name.lower() == "openai":
            return OpenAIEmbeddingProvider()
        return MockEmbeddingProvider()
