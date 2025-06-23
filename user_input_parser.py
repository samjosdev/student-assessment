import asyncio
from typing import List
from pydantic import BaseModel, Field
from model import get_extraction_llm
from prompts import EXTRACTION_PROMPT
from pdf_parser import EnhancedPDFParser
from build_graph import SubjectPerformance

class PerformanceInfo(BaseModel):
    """Tool for extracting performance information from student data."""
    subjects: List[SubjectPerformance] = Field(description="List of subjects, their scores, and any recommended skills.")

async def extract_subjects_from_pdf(pdf_path: str) -> List[SubjectPerformance]:
    """
    Orchestrates the end-to-end process of parsing a PDF and extracting
    structured subject and score data using multiple strategies.

    Args:
        pdf_path: The path to the student's PDF report.

    Returns:
        A list of SubjectPerformance objects.
    """
    # 1. Get raw text using the enhanced, multi-strategy PDF parser
    print(f"--- Parsing PDF with enhanced parser: {pdf_path} ---")
    parser = EnhancedPDFParser()
    parsed_text = await parser.parse_pdf_report(pdf_path)
    
    if not parsed_text or not parsed_text.strip():
        print("--- PDF parsing yielded no text. ---")
        return []

    # 2. Use a structured LLM call to extract subjects and scores
    print("--- Extracting subjects and scores from parsed text ---")
    extraction_llm = get_extraction_llm().with_structured_output(PerformanceInfo)
    
    prompt = EXTRACTION_PROMPT.format(parsed_text=parsed_text)
    
    try:
        extraction_result = await extraction_llm.ainvoke(prompt)
        print(f"--- Extraction complete. Found {len(extraction_result.subjects)} subjects. ---")
        return extraction_result.subjects
    except Exception as e:
        print(f"--- Error during subject extraction: {e} ---")
        return [] 