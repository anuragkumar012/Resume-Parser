from sqlalchemy.orm import Session
from resume_ai.database import models
import json

def get_job_description(db: Session, job_id: int):
    return db.query(models.JobDescriptionDB).filter(models.JobDescriptionDB.id == job_id).first()

def get_job_description_by_text(db: Session, raw_text: str):
    """Finds an existing Job Description matching the raw text to avoid duplicate entries."""
    if not raw_text:
        return None
    # Compare trimmed texts
    cleaned_text = raw_text.strip()
    return db.query(models.JobDescriptionDB).filter(models.JobDescriptionDB.raw_text == cleaned_text).first()

def get_job_descriptions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.JobDescriptionDB).order_by(models.JobDescriptionDB.created_at.desc()).offset(skip).limit(limit).all()

def create_job_description(db: Session, title: str, raw_text: str, parsed_json: dict):
    # Check if identical JD already exists
    existing = get_job_description_by_text(db, raw_text)
    if existing:
        return existing

    db_jd = models.JobDescriptionDB(
        title=title or "Untitled Role",
        raw_text=raw_text.strip(),
        parsed_json=json.dumps(parsed_json)
    )
    db.add(db_jd)
    db.commit()
    db.refresh(db_jd)
    return db_jd

def get_candidate(db: Session, candidate_id: int):
    return db.query(models.CandidateDB).filter(models.CandidateDB.id == candidate_id).first()

def get_candidate_by_email(db: Session, email: str):
    if not email:
        return None
    return db.query(models.CandidateDB).filter(models.CandidateDB.email == email.strip().lower()).first()

def get_candidates(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CandidateDB).order_by(models.CandidateDB.created_at.desc()).offset(skip).limit(limit).all()

def create_candidate(db: Session, name: str, email: str, phone: str, raw_resume_text: str, parsed_json: dict):
    # Check if candidate email already exists (update record if exists, or create new)
    db_candidate = None
    if email:
        db_candidate = get_candidate_by_email(db, email)
        
    if db_candidate:
        # Update existing candidate details
        db_candidate.name = name or db_candidate.name
        db_candidate.phone = phone or db_candidate.phone
        db_candidate.raw_resume_text = raw_resume_text or db_candidate.raw_resume_text
        db_candidate.parsed_json = json.dumps(parsed_json)
    else:
        db_candidate = models.CandidateDB(
            name=name or "Unknown Candidate",
            email=email.strip().lower() if email else None,
            phone=phone or None,
            raw_resume_text=raw_resume_text,
            parsed_json=json.dumps(parsed_json)
        )
        db.add(db_candidate)
        
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def get_match_report(db: Session, report_id: int):
    return db.query(models.MatchReportDB).filter(models.MatchReportDB.id == report_id).first()

def get_match_reports(db: Session, job_id: int = None, skip: int = 0, limit: int = 100):
    query = db.query(models.MatchReportDB)
    if job_id is not None:
        query = query.filter(models.MatchReportDB.job_id == job_id)
    return query.order_by(models.MatchReportDB.ats_score.desc()).offset(skip).limit(limit).all()

def create_match_report(db: Session, candidate_id: int, job_id: int, ats_score: float, 
                        semantic_score: float, skill_match: float, experience_match: float,
                        education_match: float, keyword_match: float, eligibility: str,
                        eligibility_reasons: list, full_report: dict):
    # Check if a report for this specific candidate and job already exists. 
    # If so, update it instead of creating a duplicate.
    db_report = db.query(models.MatchReportDB).filter(
        models.MatchReportDB.candidate_id == candidate_id,
        models.MatchReportDB.job_id == job_id
    ).first()

    reasons_str = json.dumps(eligibility_reasons) if eligibility_reasons else "[]"
    
    if db_report:
        db_report.ats_score = ats_score
        db_report.semantic_score = semantic_score
        db_report.skill_match = skill_match
        db_report.experience_match = experience_match
        db_report.education_match = education_match
        db_report.keyword_match = keyword_match
        db_report.eligibility = eligibility
        db_report.eligibility_reasons = reasons_str
        db_report.full_report_json = json.dumps(full_report)
    else:
        db_report = models.MatchReportDB(
            candidate_id=candidate_id,
            job_id=job_id,
            ats_score=ats_score,
            semantic_score=semantic_score,
            skill_match=skill_match,
            experience_match=experience_match,
            education_match=education_match,
            keyword_match=keyword_match,
            eligibility=eligibility,
            eligibility_reasons=reasons_str,
            full_report_json=json.dumps(full_report)
        )
        db.add(db_report)
        
    db.commit()
    db.refresh(db_report)
    return db_report
