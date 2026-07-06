import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import io
from sqlalchemy.orm import Session

from resume_ai.database.db import get_db, init_db
from resume_ai.database import crud
from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.models.scoring_schema import (
    MatchReport,
    ATSScoreResult,
    EligibilityResult,
    SkillGapResult,
    ExperienceAnalysisResult,
    KeywordAnalysisResult,
    ResumeQualityResult,
    RecommendationItem
)
from resume_ai.parser.resume_parser import parse_resume_pipeline_async
from resume_ai.ai.llm import parse_jd_async, analyze_resume_quality_llm_async
from resume_ai.matcher.skill_match import analyze_skills
from resume_ai.matcher.experience_match import analyze_experience
from resume_ai.matcher.education_match import analyze_education
from resume_ai.matcher.semantic_match import calculate_semantic_matching
from resume_ai.matcher.ats_score import compute_ats_score
from resume_ai.matcher.eligibility import check_eligibility
from resume_ai.matcher.embeddings import get_embeddings, cosine_similarity
from resume_ai.utils.report_generator import generate_pdf_report, export_candidates_to_excel

# Initialize FastAPI App
app = FastAPI(
    title="Resume Intelligence Platform API",
    description="Production-ready ATS parser, match scoring, and eligibility check system.",
    version="1.0.0"
)

# Enable CORS for Recruiter Dashboard compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing database tables...")
    init_db()
    
    # Seed default sandbox users
    db = next(get_db())
    try:
        from resume_ai.database.models import UserDB
        
        # Clean up old admin user
        admin_user = db.query(UserDB).filter(UserDB.email == "admin@resumeintel.com").first()
        if admin_user:
            db.delete(admin_user)
            db.commit()
            logger.info("Removed old admin user.")
            
        # Seed candidate user
        candidate_user = db.query(UserDB).filter(UserDB.email == "candidate@resumeintel.com").first()
        if not candidate_user:
            crud.create_user(db, email="candidate@resumeintel.com", password_raw="candidate123", role="candidate")
            logger.info("Candidate user seeded successfully.")
            
        # Seed company user
        company_user = db.query(UserDB).filter(UserDB.email == "hr@company.com").first()
        if not company_user:
            crud.create_user(db, email="hr@company.com", password_raw="company123", role="company")
            logger.info("Company user seeded successfully.")
            
    except Exception as e:
        logger.error(f"Failed to seed default sandbox users: {e}")
    finally:
        db.close()


@app.get("/")
def read_root():
    return {"status": "online", "message": "Resume Intelligence Platform API is running."}


class LoginRequest(BaseModel):
    email: str
    password: str
    role: str


@app.post("/api/login", summary="User Login Authentication")
def api_login(request: LoginRequest, db: Session = Depends(get_db)):
    logger.info(f"Login attempt: {request.email} as {request.role}")
    user = crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=401, detail="User account not found.")
    
    # Verify hashed password
    hashed_input = crud.hash_password(request.password)
    if user.password != hashed_input:
        raise HTTPException(status_code=401, detail="Incorrect password.")
    
    # Verify role match
    if user.role != request.role:
        raise HTTPException(
            status_code=401,
            detail=f"Access denied. User role does not match request ({request.role})."
        )
    
    return {
        "status": "success",
        "user": {
            "email": user.email,
            "role": user.role
        }
    }

@app.post("/parse_resume", response_model=ResumeData, summary="Parse a PDF Resume")
async def api_parse_resume(file: UploadFile = File(...)):
    """Uploads a PDF resume, extracts/cleans the text, and parses it into structured ResumeData JSON."""
    logger.info(f"API call: /parse_resume - File: {file.filename}")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        contents = await file.read()
        pipeline_result = await parse_resume_pipeline_async(contents)
        return pipeline_result["resume_data"]
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse resume: {str(e)}")

@app.post("/parse_job", response_model=JobDescriptionData, summary="Parse Job Description Text")
async def api_parse_job(jd_text: str = Form(...)):
    """Parses raw job description text into a structured JobDescriptionData schema."""
    logger.info("API call: /parse_job")
    try:
        return await parse_jd_async(jd_text)
    except Exception as e:
        logger.error(f"Error parsing JD: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse Job Description: {str(e)}")

class MatchRequest(BaseModel):
    candidate: ResumeData
    job: JobDescriptionData

@app.post("/match", summary="Match Resume against JD (Similarity Metrics)")
async def api_match(request: MatchRequest):
    """Computes semantic overlap metrics across resume and job description sections."""
    logger.info("API call: /match")
    try:
        semantic_sims = calculate_semantic_matching(request.candidate, request.job)
        skill_res = analyze_skills(request.candidate, request.job)
        exp_res = analyze_experience(request.candidate, request.job)
        edu_res = analyze_education(request.candidate, request.job)
        
        return {
            "semantic_score": semantic_sims["overall_similarity"],
            "skill_match": skill_res["skill_match_score"],
            "experience_match": exp_res["experience_match_score"],
            "education_match": edu_res["education_match_score"],
            "semantic_section_details": semantic_sims
        }
    except Exception as e:
        logger.error(f"Error matching profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/eligibility", response_model=EligibilityResult, summary="Check Candidate Eligibility")
async def api_eligibility(request: MatchRequest):
    """Runs filter rules (experience, education, visa, location, notice period) to check candidate suitability."""
    logger.info("API call: /eligibility")
    try:
        # Dependency modules
        skill_res = analyze_skills(request.candidate, request.job)
        exp_res = analyze_experience(request.candidate, request.job)
        edu_res = analyze_education(request.candidate, request.job)
        
        res = check_eligibility(request.candidate, request.job, skill_res, exp_res, edu_res)
        return EligibilityResult(
            status=res["eligibility"],
            reasons=res["eligibility_reasons"]
        )
    except Exception as e:
        logger.error(f"Error checking eligibility: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

class ATSScoreRequest(BaseModel):
    candidate: ResumeData
    job: JobDescriptionData
    resume_text: str

@app.post("/ats_score", response_model=ATSScoreResult, summary="Calculate ATS Weighted Score")
async def api_ats_score(request: ATSScoreRequest):
    """Calculates weighted ATS compatibility score out of 100 based on standard scorecard weights."""
    logger.info("API call: /ats_score")
    try:
        # Run sub-modules
        semantic_sims = calculate_semantic_matching(request.candidate, request.job)
        skill_res = analyze_skills(request.candidate, request.job)
        exp_res = analyze_experience(request.candidate, request.job)
        edu_res = analyze_education(request.candidate, request.job)
        
        return compute_ats_score(
            request.candidate,
            request.job,
            request.resume_text,
            skill_res,
            exp_res,
            edu_res,
            semantic_sims
        )
    except Exception as e:
        logger.error(f"Error scoring ATS match: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=MatchReport, summary="End-to-End Analysis (Parser + Score + QA)")
async def api_analyze(file: UploadFile = File(...), jd_text: str = Form(...), db: Session = Depends(get_db)):
    """
    End-to-end evaluation. Upload PDF resume and raw Job Description.
    Runs text extraction, LLM parsing, semantic matching, eligibility checking, skill gap calculation,
    resume style checking, and returns a unified dashboard report.
    """
    logger.info(f"API call: /analyze - File: {file.filename}")
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        # Step 1: Extract and clean raw PDF text to check DB for existing candidate
        contents = await file.read()
        from resume_ai.parser.pdf_reader import extract_text_from_pdf
        from resume_ai.parser.text_cleaner import clean_text
        raw_text_extracted = extract_text_from_pdf(contents)
        raw_resume_text = clean_text(raw_text_extracted)
        
        # Find if candidate is already parsed in DB
        from resume_ai.database import models
        db_candidate = db.query(models.CandidateDB).filter(models.CandidateDB.raw_resume_text == raw_resume_text).first()
        
        if db_candidate and db_candidate.parsed_json:
            logger.info("Found pre-parsed candidate in DB. Skipping LLM resume parsing.")
            resume_data = ResumeData.model_validate_json(db_candidate.parsed_json)
            resume_data.llm_usage = None
        else:
            # Parse via LLM pipeline
            resume_pipeline = await parse_resume_pipeline_async(contents)
            resume_data = resume_pipeline["resume_data"]
            raw_resume_text = resume_pipeline["raw_text"]
            db_candidate = None
            
        # Step 2: Skip Job Description and Quality Analysis parsing if already cached
        db_jd = crud.get_job_description_by_text(db, jd_text)
        if db_jd and db_jd.parsed_json:
            logger.info("Found pre-parsed Job Description in DB. Skipping LLM JD parsing.")
            jd_data = JobDescriptionData.model_validate_json(db_jd.parsed_json)
            jd_data.llm_usage = None
            jd_task = None
        else:
            jd_task = parse_job_description_direct(jd_text)
            
        # Check if we can reuse Quality Analysis for this candidate
        qa_result = None
        recommendations = []
        qa_task = None
        
        if db_candidate:
            prior_report = db.query(models.MatchReportDB).filter(
                models.MatchReportDB.candidate_id == db_candidate.id,
                models.MatchReportDB.full_report_json.isnot(None)
            ).first()
            if prior_report:
                try:
                    prior_data = json.loads(prior_report.full_report_json)
                    if prior_data.get("quality_analysis") and prior_data.get("recommendations"):
                        logger.info("Found prior Quality Analysis for this candidate in DB. Skipping LLM QA call.")
                        from resume_ai.models.scoring_schema import ResumeQualityResult, RecommendationItem
                        qa_result = ResumeQualityResult.model_validate(prior_data["quality_analysis"])
                        recommendations = [RecommendationItem.model_validate(r) for r in prior_data["recommendations"]]
                        qa_result.llm_usage = None
                except Exception as ex:
                    logger.warning(f"Failed to reuse prior Quality Analysis: {ex}")
                    
        if qa_result is None:
            qa_task = analyze_resume_quality_direct(raw_resume_text)
            
        # Execute any pending LLM tasks in parallel
        pending_tasks = []
        task_indices = {}
        
        if jd_task is not None:
            task_indices["jd"] = len(pending_tasks)
            pending_tasks.append(jd_task)
            
        if qa_task is not None:
            task_indices["qa"] = len(pending_tasks)
            pending_tasks.append(qa_task)
            
        if pending_tasks:
            task_results = await asyncio.gather(*pending_tasks)
            if "jd" in task_indices:
                jd_data = task_results[task_indices["jd"]]
            if "qa" in task_indices:
                qa_result, recommendations = task_results[task_indices["qa"]]
                
        # Save Job Description to DB if it is new
        if not db_jd:
            db_jd = crud.create_job_description(
                db, 
                title=jd_data.title, 
                raw_text=jd_text, 
                parsed_json=jd_data.model_dump()
            )
            
        # Save/Update Candidate in DB
        db_candidate = crud.create_candidate(
            db,
            name=resume_data.candidate_info.name,
            email=resume_data.candidate_info.email,
            phone=resume_data.candidate_info.phone,
            raw_resume_text=raw_resume_text,
            parsed_json=resume_data.model_dump()
        )
        
        # Step 3: Run matching algorithms
        semantic_sims = calculate_semantic_matching(resume_data, jd_data)
        skill_res = analyze_skills(resume_data, jd_data)
        exp_res = analyze_experience(resume_data, jd_data)
        edu_res = analyze_education(resume_data, jd_data)
        
        # Step 4: Run ATS and Eligibility score
        ats_result = compute_ats_score(
            resume_data, jd_data, raw_resume_text, skill_res, exp_res, edu_res, semantic_sims
        )
        elig_res = check_eligibility(resume_data, jd_data, skill_res, exp_res, edu_res)
        
        # Step 5: Gather gaps and keyword density
        # Keyword density match
        from resume_ai.matcher.ats_score import calculate_keyword_score
        kw_match_score = calculate_keyword_score(raw_resume_text, jd_data.keywords)
        
        # Skills details mapping
        skill_gap = SkillGapResult(
            missing_skills=skill_res["missing_required_skills"],
            weak_skills=skill_res["weak_skills"],
            strong_skills=skill_res["strong_skills"],
            transferable_skills=skill_res["transferable_skills"],
            emerging_skills=skill_res["emerging_skills"]
        )
        
        # Experience analysis mapping
        exp_analysis = ExperienceAnalysisResult(
            total_experience_years=exp_res["total_experience_years"],
            relevant_experience_years=exp_res["relevant_experience_years"],
            leadership_experience_years=exp_res["leadership_experience_years"],
            domain_experience_years=exp_res["domain_experience_years"],
            average_job_duration_months=exp_res["average_job_duration_months"],
            employment_gaps=exp_res["employment_gaps"],
            frequent_job_changes=exp_res["frequent_job_changes"]
        )
        
        # Keyword analysis mapping
        kw_density = {}
        tokens = raw_resume_text.lower().split()
        total_tokens = len(tokens) if tokens else 1
        for kw in jd_data.keywords:
            count = raw_resume_text.lower().count(kw.lower())
            if count > 0:
                kw_density[kw] = round((count / total_tokens) * 100.0, 3)
                
        kw_analysis = KeywordAnalysisResult(
            ats_keywords=jd_data.keywords,
            missing_keywords=skill_res["missing_required_skills"], # proxy for missing technical terms
            keyword_density=kw_density,
            important_phrases=skill_res["strong_skills"][:5],
            industry_terms=jd_data.keywords[:10]
        )
        
        # Identify strengths & weaknesses lists
        strengths = []
        if elig_res["eligibility"] == "Eligible":
            strengths.append("Meets all structural filter constraints.")
        if len(skill_res["strong_skills"]) >= 5:
            strengths.append(f"Strong overlap on tech stack ({len(skill_res['strong_skills'])} matching skills).")
        if exp_res["relevant_experience_years"] >= (jd_data.min_experience_years or 0.0):
            strengths.append(f"Meets or exceeds minimum required relevant years of experience.")
            
        weaknesses = []
        if elig_res["eligibility"] == "Not Eligible":
            weaknesses.append("Fails one or more mandatory eligibility requirements.")
        if skill_res["missing_required_skills"]:
            weaknesses.append(f"Missing {len(skill_res['missing_required_skills'])} core skills required for the role.")
        if exp_res["frequent_job_changes"]:
            weaknesses.append("Candidate shows a pattern of short-tenure job changes (job hopping).")
        if exp_res["employment_gaps"]:
            weaknesses.append("Contains one or more significant gaps in employment history.")
            
        # Aggregate LLM Usage statistics
        total_prompt_tokens = 0
        total_candidate_tokens = 0
        total_tokens = 0
        total_cost_usd = 0.0
        calls = []
        
        # 1. Resume Parsing Pipeline usage
        resume_usage = resume_data.llm_usage or {}
        if resume_usage:
            total_prompt_tokens += resume_usage.get("total_prompt_tokens", 0)
            total_candidate_tokens += resume_usage.get("total_candidate_tokens", 0)
            total_tokens += resume_usage.get("total_tokens", 0)
            total_cost_usd += resume_usage.get("total_cost_usd", 0.0)
            calls.extend(resume_usage.get("calls", []))
            
        # 2. Job Description Parsing usage
        jd_usage = jd_data.llm_usage or {}
        if jd_usage:
            total_prompt_tokens += jd_usage.get("prompt_tokens", 0)
            total_candidate_tokens += jd_usage.get("candidate_tokens", 0)
            total_tokens += jd_usage.get("total_tokens", 0)
            total_cost_usd += jd_usage.get("cost_usd", 0.0)
            calls.append(jd_usage)
            
        # 3. Resume Quality Analysis usage
        qa_usage = qa_result.llm_usage or {} if qa_result else {}
        if qa_usage:
            total_prompt_tokens += qa_usage.get("prompt_tokens", 0)
            total_candidate_tokens += qa_usage.get("candidate_tokens", 0)
            total_tokens += qa_usage.get("total_tokens", 0)
            total_cost_usd += qa_usage.get("cost_usd", 0.0)
            calls.append(qa_usage)
            
        aggregated_usage = {
            "total_prompt_tokens": total_prompt_tokens,
            "total_candidate_tokens": total_candidate_tokens,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost_usd, 6),
            "calls": calls
        }
        
        logger.info(f"Gemini API Total Usage for /analyze: Tokens: {total_tokens} (Prompt: {total_prompt_tokens}, Candidate: {total_candidate_tokens}) | Cost: ${aggregated_usage['total_cost_usd']:.6f} USD")
        
        report = MatchReport(
            candidate=resume_data,
            job=jd_data,
            ats_score=ats_result.overall_score,
            semantic_score=semantic_sims["overall_similarity"],
            skill_match=skill_res["skill_match_score"],
            experience_match=exp_res["experience_match_score"],
            education_match=edu_res["education_match_score"],
            keyword_match=kw_match_score,
            eligibility=elig_res["eligibility"],
            eligibility_reasons=elig_res["eligibility_reasons"],
            confidence=ats_result.confidence,
            missing_skills=skill_res["missing_required_skills"],
            resume_strengths=strengths,
            resume_weaknesses=weaknesses,
            recommendations=recommendations,
            skill_gap_analysis=skill_gap,
            experience_analysis=exp_analysis,
            keyword_analysis=kw_analysis,
            quality_analysis=qa_result,
            llm_usage=aggregated_usage
        )

        # Save Match Report to DB
        db_report = crud.create_match_report(
            db,
            candidate_id=db_candidate.id,
            job_id=db_jd.id,
            ats_score=report.ats_score,
            semantic_score=report.semantic_score,
            skill_match=report.skill_match,
            experience_match=report.experience_match,
            education_match=report.education_match,
            keyword_match=report.keyword_match,
            eligibility=report.eligibility,
            eligibility_reasons=report.eligibility_reasons,
            full_report=report.model_dump()
        )

        report.id = db_report.id
        report.candidate_id = db_candidate.id
        report.job_id = db_jd.id
        return report
        
    except Exception as e:
        logger.error(f"Error running end-to-end analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis pipeline crashed: {str(e)}")


# Helper wrappers for parallel task executions
async def parse_job_description_direct(text: str) -> JobDescriptionData:
    return await parse_jd_async(text)

async def analyze_resume_quality_direct(text: str) -> Tuple[ResumeQualityResult, List[RecommendationItem]]:
    return await analyze_resume_quality_llm_async(text)

# --- BONUS RECRIUTER DASHBOARD FEATURES ---

@app.post("/batch_parse", summary="Batch Parse Multiple PDF Resumes")
async def api_batch_parse(files: List[UploadFile] = File(...)):
    """Concurrently parses a list of PDF resumes into structured JSON objects."""
    logger.info(f"API call: /batch_parse - Files count: {len(files)}")
    
    non_pdfs = [f.filename for f in files if not f.filename.lower().endswith('.pdf')]
    if non_pdfs:
        raise HTTPException(status_code=400, detail=f"Only PDF files allowed. Non-PDF files: {non_pdfs}")
        
    async def parse_file(f: UploadFile):
        try:
            content = await f.read()
            res = await parse_resume_pipeline_async(content)
            return {"filename": f.filename, "status": "success", "data": res["resume_data"]}
        except Exception as e:
            return {"filename": f.filename, "status": "error", "message": str(e)}
            
    tasks = [parse_file(file) for file in files]
    results = await asyncio.gather(*tasks)
    return {"parsed_count": len(files), "results": results}

@app.post("/rank", summary="Rank Multiple Resumes against a Job Description")
async def api_rank(files: List[UploadFile] = File(...), jd_text: str = Form(...), db: Session = Depends(get_db)):
    """Accepts multiple resume files and ranks them against a single Job Description, ordered by ATS Score."""
    logger.info(f"API call: /rank - Candidate Files: {len(files)}")
    
    # 1. Parse JD (checking DB first)
    db_jd = crud.get_job_description_by_text(db, jd_text)
    if db_jd and db_jd.parsed_json:
        logger.info("Batch Rank: Found pre-parsed Job Description in DB. Skipping LLM JD parsing.")
        jd_data = JobDescriptionData.model_validate_json(db_jd.parsed_json)
        jd_data.llm_usage = None
    else:
        jd_data = await parse_jd_async(jd_text)
        # Save Job Description to DB
        db_jd = crud.create_job_description(
            db, 
            title=jd_data.title, 
            raw_text=jd_text, 
            parsed_json=jd_data.model_dump()
        )
    
    async def process_candidate(f: UploadFile):
        try:
            content = await f.read()
            from resume_ai.parser.pdf_reader import extract_text_from_pdf
            from resume_ai.parser.text_cleaner import clean_text
            raw_text = extract_text_from_pdf(content)
            cleaned_text = clean_text(raw_text)
            
            # Check DB
            from resume_ai.database.db import SessionLocal
            from resume_ai.database import models
            local_db = SessionLocal()
            db_candidate = None
            try:
                db_candidate = local_db.query(models.CandidateDB).filter(models.CandidateDB.raw_resume_text == cleaned_text).first()
            finally:
                local_db.close()
                
            if db_candidate and db_candidate.parsed_json:
                logger.info(f"Batch Rank: Found pre-parsed candidate '{db_candidate.name}' in DB. Skipping parsing.")
                res_data = ResumeData.model_validate_json(db_candidate.parsed_json)
                res_data.llm_usage = None
                raw_text = cleaned_text
            else:
                pipeline = await parse_resume_pipeline_async(content)
                res_data = pipeline["resume_data"]
                raw_text = pipeline["raw_text"]
            
            # Match
            semantic_sims = calculate_semantic_matching(res_data, jd_data)
            skill_res = analyze_skills(res_data, jd_data)
            exp_res = analyze_experience(res_data, jd_data)
            edu_res = analyze_education(res_data, jd_data)
            
            ats_result = compute_ats_score(
                res_data, jd_data, raw_text, skill_res, exp_res, edu_res, semantic_sims
            )
            elig_res = check_eligibility(res_data, jd_data, skill_res, exp_res, edu_res)
            
            # Use SessionLocal to write database changes concurrently
            from resume_ai.database.db import SessionLocal
            local_db = SessionLocal()
            try:
                # Save Candidate
                db_candidate = crud.create_candidate(
                    local_db,
                    name=res_data.candidate_info.name,
                    email=res_data.candidate_info.email,
                    phone=res_data.candidate_info.phone,
                    raw_resume_text=raw_text,
                    parsed_json=res_data.model_dump()
                )
                
                # Keyword density match
                from resume_ai.matcher.ats_score import calculate_keyword_score
                kw_match_score = calculate_keyword_score(raw_text, jd_data.keywords)

                # Skills details mapping
                skill_gap = SkillGapResult(
                    missing_skills=skill_res["missing_required_skills"],
                    weak_skills=skill_res["weak_skills"],
                    strong_skills=skill_res["strong_skills"],
                    transferable_skills=skill_res["transferable_skills"],
                    emerging_skills=skill_res["emerging_skills"]
                )
                
                # Experience analysis mapping
                exp_analysis = ExperienceAnalysisResult(
                    total_experience_years=exp_res["total_experience_years"],
                    relevant_experience_years=exp_res["relevant_experience_years"],
                    leadership_experience_years=exp_res["leadership_experience_years"],
                    domain_experience_years=exp_res["domain_experience_years"],
                    average_job_duration_months=exp_res["average_job_duration_months"],
                    employment_gaps=exp_res["employment_gaps"],
                    frequent_job_changes=exp_res["frequent_job_changes"]
                )

                # Keyword analysis mapping
                kw_density = {}
                tokens = raw_text.lower().split()
                total_tokens = len(tokens) if tokens else 1
                for kw in jd_data.keywords:
                    count = raw_text.lower().count(kw.lower())
                    if count > 0:
                        kw_density[kw] = round((count / total_tokens) * 100.0, 3)

                kw_analysis = KeywordAnalysisResult(
                    ats_keywords=jd_data.keywords,
                    missing_keywords=skill_res["missing_required_skills"],
                    keyword_density=kw_density,
                    important_phrases=skill_res["strong_skills"][:5],
                    industry_terms=jd_data.keywords[:10]
                )

                strengths = []
                if elig_res["eligibility"] == "Eligible":
                    strengths.append("Meets all structural filter constraints.")
                if len(skill_res["strong_skills"]) >= 5:
                    strengths.append(f"Strong overlap on tech stack ({len(skill_res['strong_skills'])} matching skills).")
                if exp_res["relevant_experience_years"] >= (jd_data.min_experience_years or 0.0):
                    strengths.append(f"Meets or exceeds minimum required relevant years of experience.")
                    
                weaknesses = []
                if elig_res["eligibility"] == "Not Eligible":
                    weaknesses.append("Fails one or more mandatory eligibility requirements.")
                if skill_res["missing_required_skills"]:
                    weaknesses.append(f"Missing {len(skill_res['missing_required_skills'])} core skills required for the role.")
                if exp_res["frequent_job_changes"]:
                    weaknesses.append("Candidate shows a pattern of short-tenure job changes (job hopping).")
                if exp_res["employment_gaps"]:
                    weaknesses.append("Contains one or more significant gaps in employment history.")

                # Recommendations list empty
                recommendations = []

                # Aggregate LLM usage stats
                total_prompt_tokens = 0
                total_candidate_tokens = 0
                total_tokens = 0
                total_cost_usd = 0.0
                calls = []
                
                # 1. Resume Parsing Pipeline usage
                resume_usage = res_data.llm_usage or {}
                if resume_usage:
                    total_prompt_tokens += resume_usage.get("total_prompt_tokens", 0)
                    total_candidate_tokens += resume_usage.get("total_candidate_tokens", 0)
                    total_tokens += resume_usage.get("total_tokens", 0)
                    total_cost_usd += resume_usage.get("total_cost_usd", 0.0)
                    calls.extend(resume_usage.get("calls", []))
                    
                # 2. Job Description Parsing usage
                jd_usage = jd_data.llm_usage or {}
                if jd_usage:
                    total_prompt_tokens += jd_usage.get("prompt_tokens", 0)
                    total_candidate_tokens += jd_usage.get("candidate_tokens", 0)
                    total_tokens += jd_usage.get("total_tokens", 0)
                    total_cost_usd += jd_usage.get("cost_usd", 0.0)
                    calls.append(jd_usage)
                    
                aggregated_usage = {
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_candidate_tokens": total_candidate_tokens,
                    "total_tokens": total_tokens,
                    "total_cost_usd": round(total_cost_usd, 6),
                    "calls": calls
                }

                # Full report payload
                report_payload = {
                    "candidate": res_data.model_dump(),
                    "job": jd_data.model_dump(),
                    "ats_score": ats_result.overall_score,
                    "semantic_score": semantic_sims["overall_similarity"],
                    "skill_match": skill_res["skill_match_score"],
                    "experience_match": exp_res["experience_match_score"],
                    "education_match": edu_res["education_match_score"],
                    "keyword_match": kw_match_score,
                    "eligibility": elig_res["eligibility"],
                    "eligibility_reasons": elig_res["eligibility_reasons"],
                    "confidence": ats_result.confidence,
                    "missing_skills": skill_res["missing_required_skills"],
                    "resume_strengths": strengths,
                    "resume_weaknesses": weaknesses,
                    "recommendations": recommendations,
                    "skill_gap_analysis": skill_gap.model_dump(),
                    "experience_analysis": exp_analysis.model_dump(),
                    "keyword_analysis": kw_analysis.model_dump(),
                    "quality_analysis": None,
                    "llm_usage": aggregated_usage
                }

                # Save report
                db_report = crud.create_match_report(
                    local_db,
                    candidate_id=db_candidate.id,
                    job_id=db_jd.id,
                    ats_score=ats_result.overall_score,
                    semantic_score=semantic_sims["overall_similarity"],
                    skill_match=skill_res["skill_match_score"],
                    experience_match=exp_res["experience_match_score"],
                    education_match=edu_res["education_match_score"],
                    keyword_match=kw_match_score,
                    eligibility=elig_res["eligibility"],
                    eligibility_reasons=elig_res["eligibility_reasons"],
                    full_report=report_payload
                )

                report_id = db_report.id
                candidate_id = db_candidate.id
            finally:
                local_db.close()
            
            return {
                "id": report_id,
                "candidate_id": candidate_id,
                "job_id": db_jd.id,
                "name": res_data.candidate_info.name or f.filename,
                "email": res_data.candidate_info.email or "N/A",
                "ats_score": ats_result.overall_score,
                "eligibility": elig_res["eligibility"],
                "reasons": elig_res["eligibility_reasons"][:2], # top 2 reasons
                "filename": f.filename,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error processing candidate rank: {e}")
            return {
                "name": f.filename,
                "status": "error",
                "message": str(e),
                "ats_score": -1.0,
                "eligibility": "Unknown"
            }
            
    tasks = [process_candidate(file) for file in files]
    results = await asyncio.gather(*tasks)
    
    # Filter errors and sort by score descending
    valid_results = [r for r in results if r["status"] == "success"]
    failed_results = [r for r in results if r["status"] == "error"]
    
    valid_results.sort(key=lambda x: x["ats_score"], reverse=True)
    
    return {
        "ranked_candidates": valid_results,
        "failed_candidates": failed_results
    }

@app.post("/duplicate_detect", summary="Detect Candidate Duplicates")
async def api_duplicate_detect(candidates: List[ResumeData]):
    """
    Checks for candidate duplicates in a list based on:
    - Exact matching email/phone number.
    - Close name similarity.
    - Structural similarity of resume skill profiles.
    """
    logger.info("API call: /duplicate_detect")
    duplicates = []
    
    # Simple nested comparison
    n = len(candidates)
    processed = set()
    
    # Pre-compute skill profiles for vector comparisons
    from resume_ai.matcher.skill_match import get_flat_resume_skills
    flat_skills = []
    for c in candidates:
        flat_skills.append(" ".join(get_flat_resume_skills(c.skills)))
        
    # Generate embeddings for skills profile to measure profile similarity
    embeddings = get_embeddings(flat_skills) if flat_skills else []
    
    for i in range(n):
        if i in processed:
            continue
        c1 = candidates[i]
        c1_name = (c1.candidate_info.name or "").lower()
        c1_email = (c1.candidate_info.email or "").lower()
        
        matches = []
        for j in range(i + 1, n):
            if j in processed:
                continue
            c2 = candidates[j]
            c2_name = (c2.candidate_info.name or "").lower()
            c2_email = (c2.candidate_info.email or "").lower()
            
            # Check criteria 1: Email overlap
            if c1_email and c1_email == c2_email:
                matches.append({"index": j, "name": c2.candidate_info.name, "reason": "Identical email address"})
                processed.add(j)
                continue
                
            # Check criteria 2: Close name match + Skill profile vector similarity
            from rapidfuzz import fuzz
            if c1_name and c2_name and fuzz.token_sort_ratio(c1_name, c2_name) >= 92:
                # verify skills vector match
                sim = cosine_similarity(embeddings[i], embeddings[j]) if embeddings else 1.0
                if sim >= 0.90:
                    matches.append({"index": j, "name": c2.candidate_info.name, "reason": "High name and skill similarity"})
                    processed.add(j)
                    
        if matches:
            duplicates.append({
                "original": {"index": i, "name": c1.candidate_info.name, "email": c1.candidate_info.email},
                "matched_duplicates": matches
            })
            
    return {"duplicates_found": len(duplicates), "details": duplicates}

@app.post("/cluster", summary="Cluster Candidates by Skill Profiles")
async def api_cluster(candidates: List[ResumeData], k: int = Query(3, description="Number of clusters")):
    """Groups candidates into cohesive clusters based on their skill set embeddings using K-Means."""
    logger.info(f"API call: /cluster - Candidates count: {len(candidates)}, Clusters: {k}")
    
    if len(candidates) < k:
        raise HTTPException(status_code=400, detail=f"Number of candidates ({len(candidates)}) must be >= k ({k}).")
        
    from resume_ai.matcher.skill_match import get_flat_resume_skills
    flat_skills = []
    for c in candidates:
        flat_skills.append(" ".join(get_flat_resume_skills(c.skills)))
        
    embeddings = get_embeddings(flat_skills)
    
    from sklearn.cluster import KMeans
    import numpy as np
    
    # Fit KMeans
    kmeans = KMeans(n_clusters=k, random_state=42, n_init='auto')
    labels = kmeans.fit_predict(np.array(embeddings))
    
    clusters = {str(cluster_id): [] for cluster_id in range(k)}
    for idx, label in enumerate(labels):
        c = candidates[idx]
        clusters[str(label)].append({
            "name": c.candidate_info.name or f"Candidate {idx}",
            "email": c.candidate_info.email or "N/A",
            "current_role": c.candidate_info.current_role or "N/A",
            "skills": get_flat_resume_skills(c.skills)[:6] # top 6 skills
        })
        
    return {"cluster_count": k, "clusters": clusters}

@app.post("/report/pdf", summary="Download Styled PDF Evaluation Report")
async def api_report_pdf(report: MatchReport):
    """Generates and streams a downloadable, styled PDF scorecard report for a candidate match."""
    logger.info("API call: /report/pdf")
    try:
        report_dict = report.model_dump()
        pdf_bytes = generate_pdf_report(report_dict)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=resume_evaluation_{report.candidate.candidate_info.name or 'report'}.pdf"}
        )
    except Exception as e:
        logger.error(f"Failed to generate PDF endpoint report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@app.post("/report/excel", summary="Export Candidate Matches to Excel")
async def api_report_excel(reports: List[MatchReport]):
    """Accepts a list of match reports and returns a downloadable Excel spreadsheet of candidate data."""
    logger.info("API call: /report/excel")
    try:
        reports_dict = [r.model_dump() for r in reports]
        excel_bytes = export_candidates_to_excel(reports_dict)
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=ats_candidates_export.xlsx"}
        )
    except Exception as e:
        logger.error(f"Failed to export Excel report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")

# --- DATABASE PERSISTENCE ENDPOINTS ---

class JobCreateRequest(BaseModel):
    title: str
    raw_text: str

@app.post("/jobs", summary="Create and Parse Job Description")
async def api_create_job(req: JobCreateRequest, db: Session = Depends(get_db)):
    """Parses and stores a new job description in MySQL."""
    try:
        jd_data = await parse_jd_async(req.raw_text)
        if not jd_data.title:
            jd_data.title = req.title
            
        db_jd = crud.create_job_description(
            db, 
            title=jd_data.title, 
            raw_text=req.raw_text, 
            parsed_json=jd_data.model_dump()
        )
        return {
            "id": db_jd.id,
            "title": db_jd.title,
            "raw_text": db_jd.raw_text,
            "created_at": db_jd.created_at,
            "parsed_json": jd_data.model_dump()
        }
    except Exception as e:
        logger.error(f"Error creating job description: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse and save job: {str(e)}")

@app.get("/jobs", summary="Get all Job Descriptions")
def api_get_jobs(db: Session = Depends(get_db)):
    """Fetches a list of all saved Job Descriptions."""
    jds = crud.get_job_descriptions(db)
    return [{
        "id": j.id,
        "title": j.title,
        "raw_text": j.raw_text,
        "created_at": j.created_at,
        "parsed_json": json.loads(j.parsed_json) if j.parsed_json else {}
    } for j in jds]

@app.get("/candidates", summary="Get all Candidate Profiles")
def api_get_candidates(db: Session = Depends(get_db)):
    """Fetches a list of all saved candidate profiles."""
    candidates = crud.get_candidates(db)
    return [{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "phone": c.phone,
        "created_at": c.created_at,
        "parsed_json": json.loads(c.parsed_json) if c.parsed_json else {}
    } for c in candidates]

@app.get("/reports", summary="Get all Match Reports")
def api_get_reports(job_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Fetches a list of all match reports, optionally filtered by Job ID."""
    reports = crud.get_match_reports(db, job_id=job_id)
    result = []
    for r in reports:
        try:
            full_report = json.loads(r.full_report_json) if r.full_report_json else {}
        except Exception:
            full_report = {}
            
        result.append({
            "id": r.id,
            "candidate_id": r.candidate_id,
            "job_id": r.job_id,
            "ats_score": r.ats_score,
            "semantic_score": r.semantic_score,
            "skill_match": r.skill_match,
            "experience_match": r.experience_match,
            "education_match": r.education_match,
            "keyword_match": r.keyword_match,
            "eligibility": r.eligibility,
            "eligibility_reasons": json.loads(r.eligibility_reasons) if r.eligibility_reasons else [],
            "candidate_name": r.candidate.name if r.candidate else "Unknown",
            "candidate_email": r.candidate.email if r.candidate else "N/A",
            "job_title": r.job.title if r.job else "Unknown Role",
            "created_at": r.created_at,
            "full_report": full_report
        })
    return result

@app.get("/reports/{report_id}", summary="Get detailed Match Report by ID")
def api_get_report_by_id(report_id: int, db: Session = Depends(get_db)):
    """Fetches the full candidate evaluation scorecard report by its database ID."""
    r = crud.get_match_report(db, report_id)
    if not r:
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        full_report = json.loads(r.full_report_json) if r.full_report_json else {}
    except Exception:
        full_report = {}
        
    # Inject database IDs
    full_report["id"] = r.id
    full_report["candidate_id"] = r.candidate_id
    full_report["job_id"] = r.job_id
    return full_report

@app.delete("/jobs/{job_id}", summary="Delete Job Description and its Match Reports")
def api_delete_job(job_id: int, db: Session = Depends(get_db)):
    """Deletes a job description and cascades deletion to all associated match reports."""
    success = crud.delete_job_description(db, job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job description not found")
    return {"status": "success", "message": f"Job description {job_id} deleted successfully."}

@app.delete("/reports/{report_id}", summary="Delete Match Report")
def api_delete_report(report_id: int, db: Session = Depends(get_db)):
    """Deletes a specific candidate evaluation match report."""
    success = crud.delete_match_report(db, report_id)
    if not success:
        raise HTTPException(status_code=404, detail="Match report not found")
    return {"status": "success", "message": f"Match report {report_id} deleted successfully."}
