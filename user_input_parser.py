from pdf_parser import EnhancedPDFParser
from typing import Dict, Optional, List
from model import get_extraction_llm
from prompts import MULTI_PARSER_EXTRACTION_PROMPT
from pydantic import BaseModel, Field

class SubjectPerformance(BaseModel):
    """Represents a student's performance in a single subject."""
    subject: str = Field(description="The subject, e.g., 'Math' or 'ELA'")
    score: int = Field(description="The student's score in the subject.")
    recommended_skills: List[str] = Field(default_factory=list, description="A list of recommended skills for the subject, if any.")

class PerformanceInfo(BaseModel):
    """Tool for extracting performance information from student data."""
    subjects: List[SubjectPerformance] = Field(description="List of subjects, their scores, and any recommended skills.")

def parse_pdf_to_text(pdf_path: str) -> Optional[tuple]:
    """
    Parses a PDF file and extracts raw text content from both PyMuPDF and LlamaParse.
    Returns a tuple: (pymupdf_text, llamaparse_text)
    """
    try:
        parser = EnhancedPDFParser()
        parsed_outputs = parser.parse_pdf_report(pdf_path)
        pymupdf_text = parsed_outputs.get('pymupdf', '')
        llamaparse_text = parsed_outputs.get('llamaparse', '')
        if not pymupdf_text and not llamaparse_text:
            return None
        if pymupdf_text:
            print(f"✅ PyMuPDF extracted {len(pymupdf_text)} characters")
        if llamaparse_text:
            print(f"✅ LlamaParse extracted {len(llamaparse_text)} characters")
        return pymupdf_text, llamaparse_text
    except Exception as e:
        print(f"--- Error during PDF parsing: {e} ---")
        return None
