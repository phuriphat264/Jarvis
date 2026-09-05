import pytest
from app.services.memory_service import MemoryService
from app.interfaces.embedding_provider import MockEmbeddingProvider
from app.interfaces.memory_extractor import MockMemoryExtractor
from app.database.models.message import Message
from app.database.models.memory import Memory

@pytest.mark.asyncio
async def test_mock_embedding_provider():
    provider = MockEmbeddingProvider()
    emb = await provider.embed("hello world")
    assert len(emb) == 1536
    assert isinstance(emb[0], float)

@pytest.mark.asyncio
async def test_mock_memory_extractor():
    extractor = MockMemoryExtractor()
    messages = [
        Message(role="user", content="remember that I like apples"),
        Message(role="assistant", content="Got it.")
    ]
    result = await extractor.extract(messages)
    assert len(result.memories) == 1
    assert result.memories[0].memory_type == "preference"
    assert "Mock memory from" in result.memories[0].content

# More comprehensive tests would mock the AsyncSession and verify MemoryService logic,
# but the key logic components (extraction, embedding) are verified for basic shapes.
