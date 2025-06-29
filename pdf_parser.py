import asyncio
import fitz  # PyMuPDF

class EnhancedPDFParser:
    """Enhanced PDF parser that uses PyMuPDF for fast and reliable text extraction."""
    
    def __init__(self):
        pass
    
    def parse_pdf_report(self, file_path: str) -> dict:
        """
        Parse PDF using PyMuPDF and LlamaParse for maximum coverage.
        Args:
            file_path: Path to the PDF file
        Returns:
            Dict with keys: 'pymupdf',  'llamaparse'
        """
        print(f"--- Parsing PDF: {file_path} ---")
        results = {}
        
        # Only use PyMuPDF (fastest)
        print("🔄 Using PyMuPDF parser only...")
        pymupdf_text = self._parse_with_pymupdf(file_path)
        results['pymupdf'] = pymupdf_text
        print(f"✅ PyMuPDF extracted {len(pymupdf_text)} characters")
        
        # LlamaParse
        llamaparse_text = ''
        try:
            from llama_parse import LlamaParse
            print("🔄 Using LlamaParse parser...")
            parser = LlamaParse()
            job = parser.parse(file_path)
            documents = job.result()
            llamaparse_text = documents[0].text if documents else ''
            print(f"✅ LlamaParse extracted {len(llamaparse_text)} characters")
        except Exception as e:
            llamaparse_text = ''
        results['llamaparse'] = llamaparse_text
        
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