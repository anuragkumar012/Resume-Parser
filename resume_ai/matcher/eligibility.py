from typing import Dict, Any, List
from loguru import logger

from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.matcher.skill_match import match_skill_fuzzy, get_flat_resume_skills
from resume_ai.matcher.education_match import get_degree_rank

def check_eligibility(
    resume: ResumeData, 
    jd: JobDescriptionData,
    skill_match_results: Dict[str, Any],
    exp_results: Dict[str, Any],
    edu_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluates candidates against critical filters (experience, education, location, visa, notice period, skills).
    Categorizes as 'Eligible', 'Partially Eligible', or 'Not Eligible' with reasons.
    """
    logger.info("Evaluating candidate eligibility filters.")
    
    reasons: List[str] = []
    status = "Eligible"
    
    # 1. Check Mandatory Skills
    # Check if any mandatory requirement matches candidate skills
    candidate_skills = get_flat_resume_skills(resume.skills)
    missing_mandatory = []
    
    for req in jd.mandatory_requirements:
        is_matched = False
        req_clean = req.lower()
        
        # If the requirement mentions specific technologies
        tech_words = ["python", "react", "java", "kubernetes", "docker", "aws", "c++", "c#", "golang", "angular", "sql"]
        detected_techs = [t for t in tech_words if t in req_clean]
        
        if detected_techs:
            for tech in detected_techs:
                # does candidate have this tech?
                if any(match_skill_fuzzy(s, tech) for s in candidate_skills):
                    is_matched = True
                    break
            if not is_matched:
                missing_mandatory.append(f"Missing required tech from requirement: '{req}'")
        else:
            # Check general semantic or phrase match
            # If the requirement doesn't mention specific tech, it might be a general constraint (e.g. Visa)
            pass
            
    if missing_mandatory:
        reasons.extend(missing_mandatory)
        status = "Partially Eligible"  # missing mandatory skills flags partial or not eligible
        
    # 2. Check Experience Bounds
    min_exp = jd.min_experience_years or 0.0
    cand_rel_exp = exp_results.get("relevant_experience_years", 0.0)
    cand_tot_exp = exp_results.get("total_experience_years", 0.0)
    
    if min_exp > 0:
        if cand_rel_exp < min_exp * 0.5:
            reasons.append(
                f"Experience gap: Has {cand_rel_exp} years of relevant experience, but role requires {min_exp} years."
            )
            status = "Not Eligible"
        elif cand_rel_exp < min_exp:
            reasons.append(
                f"Slightly under-experienced: Has {cand_rel_exp} years relevant experience, while {min_exp} is requested."
            )
            if status != "Not Eligible":
                status = "Partially Eligible"
                
    # 3. Check Education Degree Level
    edu_ok = edu_results.get("meets_education_requirement", True)
    highest_rank = edu_results.get("highest_degree_rank", 0)
    
    # Calculate required rank
    required_rank = 0
    if jd.required_education:
        for re_degree in jd.required_education:
            rank = get_degree_rank(re_degree)
            if rank > required_rank:
                required_rank = rank
                
    if not edu_ok and required_rank > 0:
        if highest_rank < required_rank - 1:
            reasons.append(
                f"Education gap: Highest degree rank ({highest_rank}) is significantly lower than required ({required_rank})."
            )
            status = "Not Eligible"
        else:
            reasons.append(
                f"Education level mismatch: Highest degree is below preferred degree."
            )
            if status != "Not Eligible":
                status = "Partially Eligible"
                
    # 4. Check Location and Remote Preferences
    jd_loc = (jd.location or "").lower()
    cand_pref_loc = (resume.candidate_info.preferred_location or "").lower()
    cand_remote_pref = (resume.candidate_info.remote_preference or "").lower()
    
    if jd_loc and cand_remote_pref == "onsite" and cand_pref_loc:
        # If JD is in London and candidate preferred location is in New York (onsite only)
        # We check fuzzy city overlap
        if jd_loc not in cand_pref_loc and cand_pref_loc not in jd_loc:
            reasons.append(
                f"Location mismatch: Candidate prefers {resume.candidate_info.preferred_location} (Onsite), but job is in {jd.location}."
            )
            if status != "Not Eligible":
                status = "Partially Eligible"
                
    # 5. Check Visa Constraints
    # If JD lists citizenship / sponsorship constraints
    jd_needs_citizen = any("citizen" in req.lower() or "clearance" in req.lower() or "sponsorship" in req.lower() for req in jd.mandatory_requirements)
    cand_visa = (resume.candidate_info.visa_status or "").lower()
    cand_auth = (resume.candidate_info.work_authorization or "").lower()
    
    if jd_needs_citizen:
        # If candidate work authorization mentions visa types (like H1B, OPT) or need sponsorship
        if "h1b" in cand_visa or "opt" in cand_visa or "sponsorship" in cand_auth.lower() or "sponsorship" in cand_visa:
            reasons.append(
                "Visa status: Candidate requires sponsorship or is on a visa (H1B/OPT), but job requires citizenship/no-sponsorship."
            )
            status = "Not Eligible"
            
    # 6. Check Notice Period
    notice_days = resume.candidate_info.notice_period_days or 0
    if notice_days > 90:
        reasons.append(
            f"Notice period: Notice period is {notice_days} days, which exceeds standard 90-day threshold."
        )
        if status == "Eligible":
            status = "Partially Eligible"
            
    # If no negative flags were raised
    if not reasons:
        reasons.append("Candidate meets all mandatory experience, education, skill, and location requirements.")
        
    return {
        "eligibility": status,
        "eligibility_reasons": reasons
    }
