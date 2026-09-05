import io
import logging
from typing import Optional

logger = logging.getLogger("jarvis.vision.pdf_renderer")

class PDFRenderer:
    @staticmethod
    def render_page(file_path: str, page_number: int, dpi: int = 150) -> Optional[bytes]:
        """
        Render a specific page of a PDF as a PNG image in memory.
        Returns bytes of the PNG image or None if failed.
        page_number is 1-indexed.
        """
        try:
            import fitz # PyMuPDF
            
            # fitz is 0-indexed
            fitz_page_index = page_number - 1
            
            with fitz.open(file_path) as doc:
                if fitz_page_index < 0 or fitz_page_index >= len(doc):
                    return None
                    
                page = doc.load_page(fitz_page_index)
                
                # zoom factor based on DPI (default usually 72 dpi)
                zoom = dpi / 72.0
                mat = fitz.Matrix(zoom, zoom)
                
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                return pix.tobytes("png")
                
        except Exception as e:
            logger.error(f"Failed to render PDF page {page_number}: {str(e)}")
            return None
