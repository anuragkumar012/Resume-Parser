import os
import time
import asyncio
from typing import Type, TypeVar, Optional, List, Tuple
from dotenv import load_dotenv
import google.generativeai as genai
from pydantic import BaseModel, ValidationError
from loguru import logger

from resume_ai.ai.prompts import (
    RESUME_PARSER_SYSTEM_PROMPT,
    JD_PARSER_SYSTEM_PROMPT,
    QUALITY_ANALYSIS_SYSTEM_PROMPT,
)
from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.models.scoring_schema import ResumeQualityResult, RecommendationItem

# Load environment variables
load_dotenv()

# Configuration settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-1.5-flash")
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))

# Configure Google Generative AI
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("GEMINI_API_KEY is not set in environment. Gemini operations will fail.")

T = TypeVar("T", bound=BaseModel)

def resolve_schema_refs(schema, defs=None):
    """
    Recursively resolves $ref schemas inline, sets 'nullable': True for anyOf [Type, null] unions,
    and strips unsupported fields (default, title, additionalProperties) to fit Gemini strict schema rules.
    """
    if defs is None:
        defs = schema.get("$defs", {})
        
    if isinstance(schema, dict):
        if "properties" in schema and isinstance(schema["properties"], dict):
            schema["properties"].pop("llm_usage", None)
        # Handle Pydantic v2 Optional fields (anyOf: [type, null])
        if "anyOf" in schema and isinstance(schema["anyOf"], list):
            non_null_schemas = [item for item in schema["anyOf"] if isinstance(item, dict) and item.get("type") != "null"]
            if len(non_null_schemas) == 1:
                resolved_non_null = resolve_schema_refs(non_null_schemas[0], defs)
                cleaned = {"nullable": True}
                cleaned.update(resolved_non_null)
                cleaned.pop("anyOf", None)
                return cleaned
            elif len(non_null_schemas) > 1:
                resolved_first = resolve_schema_refs(non_null_schemas[0], defs)
                cleaned = {}
                cleaned.update(resolved_first)
                return cleaned

        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            ref_schema = defs.get(ref_name, {})
            return resolve_schema_refs(ref_schema, defs)
            
        cleaned = {}
        for k, v in schema.items():
            if k == "properties" and isinstance(v, dict):
                cleaned[k] = {prop_name: resolve_schema_refs(prop_schema, defs) for prop_name, prop_schema in v.items()}
            elif k in ("$defs", "default", "title", "additionalProperties"):
                continue
            else:
                cleaned[k] = resolve_schema_refs(v, defs)
            
        # Capitalize type strings for Gemini compatibility
        if "type" in cleaned and isinstance(cleaned["type"], str):
            cleaned["type"] = cleaned["type"].upper()
            
        return cleaned
        
    elif isinstance(schema, list):
        return [resolve_schema_refs(item, defs) for item in schema]
        
    return schema


def calculate_gemini_cost(model_name: str, prompt_tokens: int, candidate_tokens: int) -> float:
    # Normalize model name
    name = model_name.lower().replace("models/", "")
    
    # Defaults to flash pricing (e.g. gemini-3.5-flash, gemini-1.5-flash, gemini-2.0-flash)
    input_rate = 0.075 / 1_000_000
    output_rate = 0.30 / 1_000_000
    
    if "pro" in name:
        # e.g., gemini-1.5-pro
        input_rate = 1.25 / 1_000_000
        output_rate = 5.00 / 1_000_000
    elif "flash" in name:
        input_rate = 0.075 / 1_000_000
        output_rate = 0.30 / 1_000_000
        
    cost = (prompt_tokens * input_rate) + (candidate_tokens * output_rate)
    return round(cost, 6)

def extract_usage(response, model_name: str, purpose: str = "") -> dict:
    try:
        usage = response.usage_metadata
        prompt_tokens = usage.prompt_token_count or 0
        candidate_tokens = usage.candidates_token_count or 0
        total_tokens = usage.total_token_count or (prompt_tokens + candidate_tokens)
    except Exception as e:
        logger.warning(f"Could not extract usage metadata from Gemini response: {e}")
        prompt_tokens = 0
        candidate_tokens = 0
        total_tokens = 0
        
    cost_usd = calculate_gemini_cost(model_name, prompt_tokens, candidate_tokens)
    
    return {
        "model_name": model_name,
        "prompt_tokens": prompt_tokens,
        "candidate_tokens": candidate_tokens,
        "total_tokens": total_tokens,
        "cost_usd": cost_usd,
        "purpose": purpose
    }

def parse_structured_output(
    prompt: str,
    system_prompt: str,
    response_model: Type[T],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    purpose: str = "",
) -> T:
    """
    Parses unstructured text using Gemini Structured Outputs (response_schema)
    synchronously, with retries on validation failure.
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured. Please set GEMINI_API_KEY in environment.")
        
    if not prompt or not prompt.strip():
        logger.error("Structured output error: prompt content is empty or blank!")
        raise ValueError("The prompt content must not be empty.")
        
    last_error = None
    model_name = model
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
        
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling Gemini ({model_name}) for structured output. Attempt {attempt}/{MAX_RETRIES}.")
            
            # Configure generative model with system instructions
            gen_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            
            # Generate a cleaned JSON schema dict from response_model to bypass GenAI SDK's serialization bugs
            raw_schema = response_model.model_json_schema()
            cleaned_schema = resolve_schema_refs(raw_schema)
            
            # Call generation with structured JSON schema
            response = gen_model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=cleaned_schema,
                    temperature=temperature
                )
            )
            
            response_text = response.text
            if not response_text:
                raise ValueError("Empty response received from Gemini.")
                
            parsed_data = response_model.model_validate_json(response_text)
            
            # Extract and inject LLM usage metadata
            usage_info = extract_usage(response, model_name, purpose=purpose or response_model.__name__)
            parsed_data.llm_usage = usage_info
            
            return parsed_data
            
        except (ValidationError, Exception) as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            last_error = e
            if attempt == MAX_RETRIES - 1 and model != FALLBACK_MODEL:
                logger.info(f"Switching to fallback model ({FALLBACK_MODEL}) for the final attempt.")
                model = FALLBACK_MODEL
                if not model.startswith("models/"):
                    model_name = f"models/{model}"
                else:
                    model_name = model
            
            sleep_time = 1
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower():
                sleep_time = 5 * attempt
                logger.info(f"Rate limit hit. Sleeping for {sleep_time}s before retrying...")
            time.sleep(sleep_time)
            
    raise last_error or RuntimeError("Structured output parsing failed.")

async def parse_structured_output_async(
    prompt: str,
    system_prompt: str,
    response_model: Type[T],
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    purpose: str = "",
) -> T:
    """
    Parses unstructured text using Gemini Structured Outputs (response_schema)
    asynchronously, with retries on validation failure.
    """
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API key not configured. Please set GEMINI_API_KEY in environment.")
        
    if not prompt or not prompt.strip():
        logger.error("Structured output error: prompt content is empty or blank!")
        raise ValueError("The prompt content must not be empty.")
        
    last_error = None
    model_name = model
    if not model_name.startswith("models/"):
        model_name = f"models/{model_name}"
        
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Calling Async Gemini ({model_name}) for structured output. Attempt {attempt}/{MAX_RETRIES}.")
            
            gen_model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt
            )
            
            # Generate a cleaned JSON schema dict from response_model to bypass GenAI SDK's serialization bugs
            raw_schema = response_model.model_json_schema()
            cleaned_schema = resolve_schema_refs(raw_schema)
            
            # Generate content asynchronously
            response = await gen_model.generate_content_async(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=cleaned_schema,
                    temperature=temperature
                )
            )
            
            response_text = response.text
            if not response_text:
                raise ValueError("Empty response received from Gemini.")
                
            parsed_data = response_model.model_validate_json(response_text)
            
            # Extract and inject LLM usage metadata
            usage_info = extract_usage(response, model_name, purpose=purpose or response_model.__name__)
            parsed_data.llm_usage = usage_info
            
            return parsed_data
            
        except (ValidationError, Exception) as e:
            logger.warning(f"Async Attempt {attempt} failed: {str(e)}")
            last_error = e
            if attempt == MAX_RETRIES - 1 and model != FALLBACK_MODEL:
                logger.info(f"Switching to fallback model ({FALLBACK_MODEL}) for the final attempt.")
                model = FALLBACK_MODEL
                if not model.startswith("models/"):
                    model_name = f"models/{model}"
                else:
                    model_name = model
            
            sleep_time = 1
            err_str = str(e)
            if "429" in err_str or "quota" in err_str.lower() or "limit" in err_str.lower():
                sleep_time = 5 * attempt
                logger.info(f"Rate limit hit. Sleeping for {sleep_time}s before retrying...")
            await asyncio.sleep(sleep_time)
            
    raise last_error or RuntimeError("Async structured output parsing failed.")

# High-level API wrappers

def parse_resume(text: str) -> ResumeData:
    """Parses raw resume text into ResumeData schema."""
    return parse_structured_output(
        prompt=text,
        system_prompt=RESUME_PARSER_SYSTEM_PROMPT,
        response_model=ResumeData,
        purpose="Resume Parsing",
    )

async def parse_resume_async(text: str) -> ResumeData:
    """Parses raw resume text into ResumeData schema asynchronously."""
    return await parse_structured_output_async(
        prompt=text,
        system_prompt=RESUME_PARSER_SYSTEM_PROMPT,
        response_model=ResumeData,
        purpose="Resume Parsing",
    )

def parse_jd(text: str) -> JobDescriptionData:
    """Parses raw job description text into JobDescriptionData schema."""
    from resume_ai.parser.text_cleaner import clean_jd_boilerplate
    cleaned = clean_jd_boilerplate(text)
    return parse_structured_output(
        prompt=cleaned,
        system_prompt=JD_PARSER_SYSTEM_PROMPT,
        response_model=JobDescriptionData,
        purpose="Job Description Parsing",
    )

async def parse_jd_async(text: str) -> JobDescriptionData:
    """Parses raw job description text into JobDescriptionData schema asynchronously."""
    from resume_ai.parser.text_cleaner import clean_jd_boilerplate
    cleaned = clean_jd_boilerplate(text)
    return await parse_structured_output_async(
        prompt=cleaned,
        system_prompt=JD_PARSER_SYSTEM_PROMPT,
        response_model=JobDescriptionData,
        purpose="Job Description Parsing",
    )

class QualityAnalysisWrapper(BaseModel):
    quality_analysis: ResumeQualityResult
    recommendations: List[RecommendationItem]
    llm_usage: Optional[dict] = None

def analyze_resume_quality_llm(resume_text: str) -> Tuple[ResumeQualityResult, List[RecommendationItem]]:
    """Analyzes resume quality and lists grammar, phrasing, metrics, and improvement recommendations."""
    res = parse_structured_output(
        prompt=resume_text,
        system_prompt=QUALITY_ANALYSIS_SYSTEM_PROMPT,
        response_model=QualityAnalysisWrapper,
        purpose="Resume Quality Analysis",
    )
    if hasattr(res, "llm_usage") and res.llm_usage:
        res.quality_analysis.llm_usage = res.llm_usage
    return res.quality_analysis, res.recommendations

async def analyze_resume_quality_llm_async(resume_text: str) -> Tuple[ResumeQualityResult, List[RecommendationItem]]:
    """Analyzes resume quality and lists grammar, phrasing, metrics, and improvement recommendations asynchronously."""
    res = await parse_structured_output_async(
        prompt=resume_text,
        system_prompt=QUALITY_ANALYSIS_SYSTEM_PROMPT,
        response_model=QualityAnalysisWrapper,
        purpose="Resume Quality Analysis",
    )
    if hasattr(res, "llm_usage") and res.llm_usage:
        res.quality_analysis.llm_usage = res.llm_usage
    return res.quality_analysis, res.recommendations

def transcribe_pdf_vision(pdf_bytes: bytes) -> Tuple[str, dict]:
    """
    Renders PDF pages as images and uses Gemini Vision to transcribe the text.
    Acts as a high-fidelity visual OCR fallback for scanned or image-only resumes.
    Returns a tuple of (transcribed_text, aggregated_usage_dict).
    """
    logger.info("Triggering visual OCR transcription for scanned/image-only PDF.")
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        transcribed_pages = []
        model_name = "models/gemini-3.5-flash"
        model = genai.GenerativeModel(model_name=model_name)
        
        total_prompt_tokens = 0
        total_candidate_tokens = 0
        total_tokens = 0
        total_cost_usd = 0.0
        calls = []
        
        for idx, page in enumerate(doc):
            logger.info(f"Rendering page {idx + 1} to image...")
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes(output="png")
            
            prompt = (
                "You are an expert OCR transcription engine. "
                "Extract all text from this resume image. "
                "Maintain the structure, bullet points, headers, and spacing as closely as possible. "
                "Do not add any preamble, comments, or modifications. Just output the extracted text."
            )
            
            response = model.generate_content([
                {"mime_type": "image/png", "data": img_bytes},
                prompt
            ])
            
            page_text = response.text
            if page_text:
                transcribed_pages.append(page_text)
                
            # Extract and log usage
            usage = extract_usage(response, model_name, purpose=f"Visual OCR (Page {idx + 1})")
            calls.append(usage)
            total_prompt_tokens += usage["prompt_tokens"]
            total_candidate_tokens += usage["candidate_tokens"]
            total_tokens += usage["total_tokens"]
            total_cost_usd += usage["cost_usd"]
                
        doc.close()
        full_text = "\n\n--- Page Break ---\n\n".join(transcribed_pages)
        logger.info(f"Visual OCR transcription complete. Extracted {len(full_text)} characters.")
        
        aggregated_usage = {
            "model_name": model_name,
            "prompt_tokens": total_prompt_tokens,
            "candidate_tokens": total_candidate_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost_usd, 6),
            "calls": calls
        }
        return full_text, aggregated_usage
        
    except Exception as e:
        logger.error(f"Visual OCR transcription failed: {e}")
        raise ValueError(f"Failed to transcribe scanned PDF: {e}")

async def transcribe_pdf_vision_async(pdf_bytes: bytes) -> Tuple[str, dict]:
    """
    Asynchronously renders PDF pages as images and uses Gemini Vision to transcribe the text.
    Acts as a high-fidelity visual OCR fallback for scanned or image-only resumes.
    Returns a tuple of (transcribed_text, aggregated_usage_dict).
    """
    logger.info("Triggering async visual OCR transcription for scanned/image-only PDF.")
    try:
        import fitz
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        transcribed_pages = []
        model_name = "models/gemini-3.5-flash"
        model = genai.GenerativeModel(model_name=model_name)
        
        total_prompt_tokens = 0
        total_candidate_tokens = 0
        total_tokens = 0
        total_cost_usd = 0.0
        calls = []
        
        for idx, page in enumerate(doc):
            logger.info(f"Rendering page {idx + 1} to image...")
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes(output="png")
            
            prompt = (
                "You are an expert OCR transcription engine. "
                "Extract all text from this resume image. "
                "Maintain the structure, bullet points, headers, and spacing as closely as possible. "
                "Do not add any preamble, comments, or modifications. Just output the extracted text."
            )
            
            response = await model.generate_content_async([
                {"mime_type": "image/png", "data": img_bytes},
                prompt
            ])
            
            page_text = response.text
            if page_text:
                transcribed_pages.append(page_text)
                
            # Extract and log usage
            usage = extract_usage(response, model_name, purpose=f"Visual OCR (Page {idx + 1})")
            calls.append(usage)
            total_prompt_tokens += usage["prompt_tokens"]
            total_candidate_tokens += usage["candidate_tokens"]
            total_tokens += usage["total_tokens"]
            total_cost_usd += usage["cost_usd"]
                
        doc.close()
        full_text = "\n\n--- Page Break ---\n\n".join(transcribed_pages)
        logger.info(f"Async Visual OCR transcription complete. Extracted {len(full_text)} characters.")
        
        aggregated_usage = {
            "model_name": model_name,
            "prompt_tokens": total_prompt_tokens,
            "candidate_tokens": total_candidate_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost_usd, 6),
            "calls": calls
        }
        return full_text, aggregated_usage
        
    except Exception as e:
        logger.error(f"Async Visual OCR transcription failed: {e}")
        raise ValueError(f"Failed to transcribe scanned PDF: {e}")
