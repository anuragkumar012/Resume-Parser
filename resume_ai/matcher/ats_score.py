from typing import Dict, Any, List
from loguru import logger

from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.models.scoring_schema import ATSScoreResult, CategoryScores

def calculate_keyword_score(resume_text: str, jd_keywords: List[str]) -> float:
    """Calculates keyword overlap percentage between resume and JD."""
    if not jd_keywords:
        return 100.0
        
    text_lower = resume_text.lower()
    matches = 0
    for kw in jd_keywords:
        if kw.lower() in text_lower:
            matches += 1
            
    return round((matches / len(jd_keywords)) * 100.0, 1)

def calculate_soft_skills_score(resume_soft_skills: List[str], jd_req_skills: List[str]) -> float:
    """Calculates score for soft skills based on overlaps."""
    # Common soft skills list if JD doesn't list soft skills explicitly
    common_soft_skills = {"communication", "leadership", "teamwork", "problem solving", "adaptability", "critical thinking"}
    
    # Extract soft skills from JD requirements if visible
    jd_soft = [s.lower() for s in jd_req_skills if s.lower() in common_soft_skills]
    if not jd_soft:
        jd_soft = list(common_soft_skills)
        
    resume_soft = {s.lower() for s in resume_soft_skills}
    if not resume_soft:
        return 30.0  # partial credit for general professional formatting
        
    matches = len(resume_soft.intersection(set(jd_soft)))
    # Cap score at 100, require at least 2 matches for full score
    target = min(len(jd_soft), 2)
    if target == 0:
        return 100.0
        
    return round(min(1.0, matches / target) * 100.0, 1)

def calculate_certifications_score(resume_certs: List[Any], jd_keywords: List[str]) -> float:
    """Calculates score based on certifications presence and relevance."""
    if not resume_certs:
        return 0.0
        
    # Check if any certification matches JD keywords (e.g. AWS, Kubernetes, PMP)
    has_relevant_cert = False
    jd_kw_set = {k.lower() for k in jd_keywords}
    
    for cert in resume_certs:
        cert_name_lower = cert.name.lower()
        if any(kw in cert_name_lower for kw in jd_kw_set):
            has_relevant_cert = True
            break
            
    if has_relevant_cert:
        return 100.0
    return 75.0  # Candidate has certifications, but not necessarily tailored to JD

def compute_ats_score(
    resume: ResumeData, 
    jd: JobDescriptionData,
    resume_text: str,
    skill_match_results: Dict[str, Any],
    exp_match_results: Dict[str, Any],
    edu_match_results: Dict[str, Any],
    semantic_results: Dict[str, float]
) -> ATSScoreResult:
    """
    Combines skill, experience, education, keyword, and soft skill scores
    into a weighted composite ATS score out of 100.
    """
    logger.info("Computing final ATS scorecard.")
    
    # 1. Skills Score (35%)
    skills_score = skill_match_results.get("skill_match_score", 0.0)
    
    # 2. Experience Score (30%)
    experience_score = exp_match_results.get("experience_match_score", 0.0)
    
    # 3. Projects Score (10%)
    # Blend of project count and semantic project score
    proj_semantic = semantic_results.get("projects_similarity", 0.0)
    project_count = len([exp for exp in resume.work_experience if exp.projects])
    proj_count_score = min(100.0, project_count * 50.0)  # 2+ projects is 100
    projects_score = round(proj_semantic * 0.7 + proj_count_score * 0.3, 1)
    
    # 4. Education Score (10%)
    education_score = edu_match_results.get("education_match_score", 0.0)
    
    # 5. Certifications Score (5%)
    certifications_score = calculate_certifications_score(resume.certifications, jd.keywords)
    
    # 6. Keywords Score (5%)
    keywords_score = calculate_keyword_score(resume_text, jd.keywords)
    
    # 7. Soft Skills Score (5%)
    soft_skills_score = calculate_soft_skills_score(resume.skills.soft_skills, jd.required_skills)
    
    # Calculate weighted total
    overall_score = (
        (skills_score * 0.35) +
        (experience_score * 0.30) +
        (projects_score * 0.10) +
        (education_score * 0.10) +
        (certifications_score * 0.05) +
        (keywords_score * 0.05) +
        (soft_skills_score * 0.05)
    )
    
    # Compute Confidence coefficient
    # Lower confidence if critical resume details (email/name) are missing or if resume text is extremely short
    has_contact = int(bool(resume.candidate_info.email and resume.candidate_info.name))
    text_length_factor = min(1.0, len(resume_text) / 1000.0) # short resumes yield lower confidence
    confidence = round(0.8 + 0.1 * has_contact + 0.1 * text_length_factor, 2)
    
    cat_scores = CategoryScores(
        skills_score=skills_score,
        experience_score=experience_score,
        projects_score=projects_score,
        education_score=education_score,
        certifications_score=certifications_score,
        keywords_score=keywords_score,
        soft_skills_score=soft_skills_score
    )
    
    return ATSScoreResult(
        overall_score=round(overall_score, 1),
        category_scores=cat_scores,
        confidence=confidence
    )
