import pytest
import asyncio
from app.core_service.rag.parsers import registry, DocumentContent, DocumentElement
from app.core_service.rag.chunker import StructureAwareChunker
from app.core_service.rag.context_builder import RAGContextBuilder

def test_parser_registry():
    # Test text parser
    parser = registry.get_parser("text/plain", ".txt")
    assert parser is not None
    assert parser.can_parse("text/plain", ".txt")
    
    # Test CSV parser
    parser = registry.get_parser("text/csv", ".csv")
    assert parser is not None
    assert parser.can_parse("text/csv", ".csv")
    
def test_structure_aware_chunker():
    content = DocumentContent(
        document_id="doc1",
        elements=[
            DocumentElement(text="This is paragraph 1.", page_number=1, line_start=1, line_end=1),
            DocumentElement(text="This is paragraph 2.", page_number=1, line_start=3, line_end=3),
            DocumentElement(text="This is paragraph 3 on page 2.", page_number=2, line_start=1, line_end=1)
        ]
    )
    
    chunker = StructureAwareChunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(content)
    
    assert len(chunks) > 0
    # The first chunk should have text from paragraph 1 and 2
    assert "This is paragraph 1." in chunks[0]["text"]
    assert chunks[0]["document_id"] == "doc1"
    
def test_rag_context_builder():
    chunks = [
        {
            "document_id": "doc1",
            "filename": "test.txt",
            "text": "Hello world.",
            "page_number": 1,
            "sheet_name": None,
            "slide_number": None
        }
    ]
    
    context = RAGContextBuilder.build_context(chunks)
    assert "UNTRUSTED DATA" in context
    assert "doc1" in context
    assert "test.txt" in context
    assert "Page: 1" in context
    assert "Hello world." in context
