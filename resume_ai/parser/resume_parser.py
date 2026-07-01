from typing import Union, Dict, Any, Tuple
from loguru import logger

from resume_ai.parser.pdf_reader import extract_text_from_pdf
from resume_ai.parser.text_cleaner import clean_text
from resume_ai.parser.section_detector import detect_sections
from resume_ai.ai.llm import parse_resume, parse_resume_async
from resume_ai.models.resume_schema import ResumeData

def parse_resume_pipeline(pdf_source: Union[str, bytes]) -> Dict[str, Any]:
    """
    Synchronous end-to-end resume parsing pipeline.
    Extracts text, cleans it, identifies sections, and passes to LLM for structured parsing.
    """
    logger.info("Starting synchronous resume parsing pipeline.")
    
    # Step 1: Extract Text from PDF
    raw_text = extract_text_from_pdf(pdf_source)
    logger.info(f"Extracted {len(raw_text)} characters of raw text from PDF.")
    
    ocr_usage = None
    # Trigger visual OCR if raw_text is empty or extremely short (scanned/image-only PDF)
    if len(raw_text.strip()) < 50:
        logger.info("Extracted text is empty or too short. Attempting visual OCR transcription...")
        if isinstance(pdf_source, bytes):
            pdf_bytes = pdf_source
        else:
            with open(pdf_source, "rb") as f:
                pdf_bytes = f.read()
        from resume_ai.ai.llm import transcribe_pdf_vision
        raw_text, ocr_usage = transcribe_pdf_vision(pdf_bytes)
    
    # Step 2: Clean Text
    cleaned = clean_text(raw_text)
    logger.info(f"Cleaned text, final length: {len(cleaned)} characters.")
    
    # Step 3: Detect Sections
    sections = detect_sections(cleaned)
    logger.info(f"Detected sections: {list(sections.keys())}")
    
    # Step 4: Parse with Gemini Structured Outputs
    resume_data = parse_resume(cleaned)
    logger.info("Successfully parsed resume using Gemini Structured Outputs.")
    
    # Combine usage stats
    parser_usage = resume_data.llm_usage or {}
    total_prompt_tokens = parser_usage.get("prompt_tokens", 0)
    total_candidate_tokens = parser_usage.get("candidate_tokens", 0)
    total_tokens = parser_usage.get("total_tokens", 0)
    total_cost_usd = parser_usage.get("cost_usd", 0.0)
    calls = []
    
    if ocr_usage:
        total_prompt_tokens += ocr_usage.get("prompt_tokens", 0)
        total_candidate_tokens += ocr_usage.get("candidate_tokens", 0)
        total_tokens += ocr_usage.get("total_tokens", 0)
        total_cost_usd += ocr_usage.get("cost_usd", 0.0)
        calls.extend(ocr_usage.get("calls", []))
        
    calls.append(parser_usage)
    
    combined_usage = {
        "total_prompt_tokens": total_prompt_tokens,
        "total_candidate_tokens": total_candidate_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "calls": calls
    }
    resume_data.llm_usage = combined_usage
    
    return {
        "resume_data": resume_data,
        "raw_text": cleaned,
        "sections": sections
    }

async def parse_resume_pipeline_async(pdf_source: Union[str, bytes]) -> Dict[str, Any]:
    """
    Asynchronous end-to-end resume parsing pipeline.
    Extracts text, cleans it, identifies sections, and parses asynchronously with LLM.
    """
    logger.info("Starting asynchronous resume parsing pipeline.")
    
    # Step 1: Extract Text
    raw_text = extract_text_from_pdf(pdf_source)
    logger.info(f"Async pipeline: Extracted {len(raw_text)} characters of raw text from PDF.")
    
    ocr_usage = None
    # Trigger visual OCR if raw_text is empty or extremely short (scanned/image-only PDF)
    if len(raw_text.strip()) < 50:
        logger.info("Async pipeline: Extracted text is empty or too short. Attempting visual OCR transcription...")
        if isinstance(pdf_source, bytes):
            pdf_bytes = pdf_source
        else:
            with open(pdf_source, "rb") as f:
                pdf_bytes = f.read()
        from resume_ai.ai.llm import transcribe_pdf_vision_async
        raw_text, ocr_usage = await transcribe_pdf_vision_async(pdf_bytes)
    
    # Step 2: Clean Text
    cleaned = clean_text(raw_text)
    logger.info(f"Async pipeline: Cleaned text length: {len(cleaned)} characters.")
    
    # Step 3: Detect Sections
    sections = detect_sections(cleaned)
    logger.info(f"Async pipeline: Detected sections: {list(sections.keys())}")
    
    # Step 4: Parse Asynchronously
    resume_data = await parse_resume_async(cleaned)
    logger.info("Successfully parsed resume asynchronously using Gemini Structured Outputs.")
    
    # Combine usage stats
    parser_usage = resume_data.llm_usage or {}
    total_prompt_tokens = parser_usage.get("prompt_tokens", 0)
    total_candidate_tokens = parser_usage.get("candidate_tokens", 0)
    total_tokens = parser_usage.get("total_tokens", 0)
    total_cost_usd = parser_usage.get("cost_usd", 0.0)
    calls = []
    
    if ocr_usage:
        total_prompt_tokens += ocr_usage.get("prompt_tokens", 0)
        total_candidate_tokens += ocr_usage.get("candidate_tokens", 0)
        total_tokens += ocr_usage.get("total_tokens", 0)
        total_cost_usd += ocr_usage.get("cost_usd", 0.0)
        calls.extend(ocr_usage.get("calls", []))
        
    calls.append(parser_usage)
    
    combined_usage = {
        "total_prompt_tokens": total_prompt_tokens,
        "total_candidate_tokens": total_candidate_tokens,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost_usd, 6),
        "calls": calls
    }
    resume_data.llm_usage = combined_usage
    
    return {
        "resume_data": resume_data,
        "raw_text": cleaned,
        "sections": sections
    }
