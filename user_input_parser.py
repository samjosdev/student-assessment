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

def parse_pdf_to_text(pdf_path: str) -> Optional[str]:
    """
    Parses a PDF file and extracts raw text content.
    
    Args:
        pdf_path: The path to the student's PDF report.
        
    Returns:
        Extracted text content if successful, None if parsing fails.
    """
    print(f"--- Parsing PDF with enhanced parser: {pdf_path} ---")
    
    try:
        parser = EnhancedPDFParser()
        parsed_outputs = parser.parse_pdf_report(pdf_path)
        
        # Get the PyMuPDF text (primary parser)
        pymupdf_text = parsed_outputs.get('pymupdf', '')
        
        if not pymupdf_text or pymupdf_text.strip() == '':
            print("--- PDF parsing yielded no text. ---")
            return None
            
        print(f"✅ PyMuPDF extracted {len(pymupdf_text)} characters")
        return pymupdf_text
        
    except Exception as e:
        print(f"--- Error during PDF parsing: {e} ---")
        return None

async def extract_subjects_from_pdf(pdf_path: str) -> List[SubjectPerformance]:
    """
    Complete function that parses PDF and extracts subjects using LLM.
    This is used by app.py for the pre-processing step.
    
    Args:
        pdf_path: The path to the student's PDF report.
        
    Returns:
        A list of SubjectPerformance objects.
    """
    # 1. Get raw text using the parsing function
    pymupdf_text = parse_pdf_to_text(pdf_path)
    
    if not pymupdf_text:
        print("--- PDF parsing failed, returning empty list ---")
        return []

    # 2. Use a structured LLM call to extract subjects and scores from the parsed text
    print("--- Extracting subjects and scores from parsed text ---")
    extraction_llm = get_extraction_llm().with_structured_output(PerformanceInfo)

    prompt = MULTI_PARSER_EXTRACTION_PROMPT.format(
        pymupdf_text=pymupdf_text
    )

    try:
        extraction_result = extraction_llm.invoke(prompt)
        print(f"--- Extraction complete. Found {len(extraction_result.subjects)} subjects. ---")
        return extraction_result.subjects
    except Exception as e:
        print(f"--- Error during subject extraction: {e} ---")
        return []



