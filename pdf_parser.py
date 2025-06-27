import asyncio
import fitz  # PyMuPDF

class EnhancedPDFParser:
    """Enhanced PDF parser that uses PyMuPDF for fast and reliable text extraction."""
    
    def __init__(self):
        pass
    
    def parse_pdf_report(self, file_path: str) -> dict:
        """
        Parse PDF using only PyMuPDF for maximum speed.
        Args:
            file_path: Path to the PDF file
        Returns:
            Dict with keys: 'pymupdf', 'ocr', 'llamaparse' (ocr and llamaparse will be empty)
        """
        print(f"--- Parsing PDF: {file_path} ---")
        results = {}
        
        # Only use PyMuPDF (fastest)
        print("🔄 Using PyMuPDF parser only...")
        pymupdf_text = self._parse_with_pymupdf(file_path)
        results['pymupdf'] = pymupdf_text
        print(f"✅ PyMuPDF extracted {len(pymupdf_text)} characters")
        
        print("--- PDF Parsing Complete ---")
        return results
    
    def _parse_with_pymupdf(self, file_path: str) -> str:
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