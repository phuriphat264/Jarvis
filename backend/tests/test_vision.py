import pytest
import base64
from fastapi.testclient import TestClient
from app.main import app
from app.interfaces.ocr_provider import OCRProviderFactory
from app.interfaces.vision_provider import VisionProviderFactory
from app.tools.impl.vision_analyze import VisionAnalyzeTool
from app.core_service.rag.parsers import registry as parser_registry
import os
from unittest.mock import patch, MagicMock

# Basic unit test for parsers loading
def test_image_parser_can_parse():
    parser = parser_registry.get_parser("image/png", ".png")
    assert parser is not None
    assert parser.__class__.__name__ == "ImageParser"

def test_ocr_provider_factory():
    provider = OCRProviderFactory.get_provider("mock")
    assert provider.__class__.__name__ == "MockOCRProvider"

@pytest.mark.asyncio
async def test_mock_ocr_extract():
    provider = OCRProviderFactory.get_provider("mock")
    result = await provider.extract_text(b"fake_image_data")
    assert result.text == "Mock OCR Text. Total: 48,500 THB"
    assert len(result.blocks) == 2
    assert result.blocks[0].confidence == 0.99

@pytest.mark.asyncio
async def test_mock_vision_analyze():
    provider = VisionProviderFactory.get_provider("mock")
    result = await provider.analyze_image(b"fake_image", "What is this?")
    assert "Mock vision description" in result.description
    assert len(result.observations) > 0

# A complete API test would require DB session setup which might be complex here,
# so we just test the core unit logic of the tool schema.
def test_vision_tool_schema():
    # Provide dummy db/user
    tool = VisionAnalyzeTool()
    schema = tool.get_schema()
    assert schema["type"] == "object"
    assert "file_id" in schema["properties"]
    assert "prompt" in schema["properties"]
    assert "file_id" in schema["required"]
