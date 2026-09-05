from typing import List, Dict, Any
from app.core_service.rag.parsers import DocumentContent, DocumentElement
from app.core.config import settings

class StructureAwareChunker:
    def __init__(self, chunk_size: int = None, overlap: int = None):
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.overlap = overlap or settings.RAG_CHUNK_OVERLAP
        
    def chunk(self, content: DocumentContent) -> List[Dict[str, Any]]:
        chunks = []
        current_chunk_text = ""
        current_chunk_elements = []
        
        for element in content.elements:
            element_len = len(element.text)
            
            # If a single element is too big, we should theoretically split it further, 
            # but for simplicity, we will just add it if current_chunk is empty, 
            # or start a new chunk.
            
            if len(current_chunk_text) + element_len > self.chunk_size and current_chunk_text:
                # Save current chunk
                chunks.append(self._build_chunk(content.document_id, current_chunk_text, current_chunk_elements))
                
                # Start new chunk with overlap if possible (simplified: just start fresh for structural boundary)
                current_chunk_text = element.text + "\n"
                current_chunk_elements = [element]
            else:
                current_chunk_text += element.text + "\n"
                current_chunk_elements.append(element)
                
        if current_chunk_text.strip():
            chunks.append(self._build_chunk(content.document_id, current_chunk_text, current_chunk_elements))
            
        return chunks

    def _build_chunk(self, doc_id: str, text: str, elements: List[DocumentElement]) -> Dict[str, Any]:
        # Merge metadata sensibly
        page_numbers = list(set([e.page_number for e in elements if e.page_number is not None]))
        sheet_names = list(set([e.sheet_name for e in elements if e.sheet_name is not None]))
        slide_numbers = list(set([e.slide_number for e in elements if e.slide_number is not None]))
        
        # Ranges
        row_starts = [e.row_start for e in elements if e.row_start is not None]
        row_ends = [e.row_end for e in elements if e.row_end is not None]
        line_starts = [e.line_start for e in elements if e.line_start is not None]
        line_ends = [e.line_end for e in elements if e.line_end is not None]
        
        # Phase 9: OCR metadata
        source_types = list(set([e.source_type for e in elements if getattr(e, "source_type", None) is not None]))
        source_type = "OCR" if "OCR" in source_types else "NATIVE"
        
        confidences = [e.confidence for e in elements if getattr(e, "confidence", None) is not None]
        avg_confidence = sum(confidences) / len(confidences) if confidences else None
        
        # Bbox is hard to merge conceptually, we'll just take the first or null if multiple
        bboxes = [e.bbox for e in elements if getattr(e, "bbox", None) is not None]
        block_indices = [e.block_index for e in elements if getattr(e, "block_index", None) is not None]
        
        return {
            "document_id": doc_id,
            "text": text.strip(),
            "page_number": page_numbers[0] if page_numbers else None,
            "sheet_name": sheet_names[0] if sheet_names else None,
            "slide_number": slide_numbers[0] if slide_numbers else None,
            "row_start": min(row_starts) if row_starts else None,
            "row_end": max(row_ends) if row_ends else None,
            "line_start": min(line_starts) if line_starts else None,
            "line_end": max(line_ends) if line_ends else None,
            "source_type": source_type,
            "confidence": avg_confidence,
            "bbox": bboxes[0] if bboxes else None,
            "block_index": block_indices[0] if block_indices else None
        }
