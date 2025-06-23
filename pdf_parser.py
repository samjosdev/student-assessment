import asyncio
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np
import cv2
from paddleocr import PaddleOCR
from llama_parse import LlamaParse

class EnhancedPDFParser:
    """Enhanced PDF parser that uses multiple strategies for better accuracy."""
    
    def __init__(self):
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
        # Use default LlamaParse configuration
        self.llama_parser = LlamaParse(result_type="markdown")
    
    async def parse_pdf_report(self, file_path: str) -> str:
        """
        Parse PDF using multiple strategies for maximum accuracy.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        print(f"--- Parsing PDF: {file_path} ---")
        
        # Strategy 1: Try PyMuPDF first (fastest, good for text-based PDFs)
        text_content = await self._parse_with_pymupdf(file_path)
        
        # Strategy 2: If PyMuPDF doesn't get good results, try OCR
        if not self._is_content_adequate(text_content):
            print("--- Text extraction insufficient, trying OCR ---")
            ocr_content = await self._parse_with_ocr(file_path)
            if ocr_content:
                text_content = ocr_content
        
        # Strategy 3: Fallback to LlamaParse if needed
        if not text_content.strip():
            print("--- Fallback to LlamaParse ---")
            text_content = await self._parse_with_llamaparse(file_path)
        
        print("--- PDF Parsing Complete ---")
        return text_content
    
    async def _parse_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            print(f"PyMuPDF error: {e}")
            return ""
    
    async def _parse_with_ocr(self, file_path: str) -> str:
        """Extract text using PaddleOCR."""
        try:
            doc = fitz.open(file_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Convert PIL image to OpenCV format
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Perform OCR
                result = self.ocr.ocr(img_cv, cls=True)
                
                # Extract text from OCR result
                if result and result[0]:
                    for line in result[0]:
                        if line and len(line) >= 2:
                            text += line[1][0] + "\n"
            
            doc.close()
            return text
        except Exception as e:
            print(f"OCR error: {e}")
            return ""
    
    async def _parse_with_llamaparse(self, file_path: str) -> str:
        """Fallback to LlamaParse."""
        try:
            documents = await self.llama_parser.aload_data(file_path)
            return "\n".join(doc.get_content() for doc in documents)
        except Exception as e:
            print(f"LlamaParse error: {e}")
            return ""
    
    def _is_content_adequate(self, text: str) -> bool:
        """Check if the extracted content is adequate."""
        if not text.strip():
            return False
        
        # Check for common IXL report indicators
        ixlm_indicators = ['ixl', 'diagnostic', 'score', 'grade', 'math', 'language', 'arts']
        text_lower = text.lower()
        
        # If we find at least 2 indicators, consider it adequate
        found_indicators = sum(1 for indicator in ixlm_indicators if indicator in text_lower)
        return found_indicators >= 2

# Backward compatibility functions
def get_pdf_parser():
    """Returns the enhanced PDF parser."""
    return EnhancedPDFParser()

async def parse_pdf_report(file_path: str, parser=None) -> str:
    """
    Parse PDF using the enhanced parser.
    
    Args:
        file_path: Path to the PDF file
        parser: Parser instance (optional, will create new one if not provided)
        
    Returns:
        Extracted text content
    """
    if parser is None:
        parser = EnhancedPDFParser()
    
    if isinstance(parser, EnhancedPDFParser):
        return await parser.parse_pdf_report(file_path)
    else:
        # Fallback to original LlamaParse method
        documents = await parser.aload_data(file_path)
        return "\n".join(doc.get_content() for doc in documents) 