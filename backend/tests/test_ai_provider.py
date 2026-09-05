import pytest
from app.interfaces.ai_provider import AIProviderFactory, MockAIProvider, OpenAIProvider
from app.core.config import settings

@pytest.mark.asyncio
async def test_ai_provider_factory_mock():
    provider = AIProviderFactory.get_provider("mock")
    assert isinstance(provider, MockAIProvider)

    # Test generation
    response = await provider.generate([{"role": "user", "content": "Hello"}])
    assert "MOCK mode" in response

def test_ai_provider_factory_openai():
    provider = AIProviderFactory.get_provider("openai")
    assert isinstance(provider, OpenAIProvider)
