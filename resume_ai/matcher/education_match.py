from typing import Dict, Any, List
from rapidfuzz import fuzz
from loguru import logger

from resume_ai.models.resume_schema import ResumeData, EducationDetail
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.utils.normalizer import normalize_degree

DEGREE_RANKS: Dict[str, int] = {
    "Unknown": 0,
    "High School Diploma": 1,
    "Associate's Degree": 2,
    "Bachelor's Degree": 3,
    "Master's Degree": 4,
    "Doctorate": 5
}

def get_degree_rank(degree_name: str) -> int:
    """Returns the numeric rank of a normalized degree level."""
    norm = normalize_degree(degree_name)
    return DEGREE_RANKS.get(norm, 0)

def match_major(candidate_major: str, jd_majors: List[str]) -> bool:
    """Fuzzy checks if the candidate's major matches any of the target majors."""
    if not candidate_major or not jd_majors:
        return True  # If no major requirements specified, it's a pass
        
    c_major = candidate_major.lower()
    for j_major in jd_majors:
        j_major_lower = j_major.lower()
        if j_major_lower in c_major or c_major in j_major_lower:
            return True
        # Check token sort ratio
        if fuzz.token_sort_ratio(c_major, j_major_lower) >= 80:
            return True
            
    return False

def analyze_education(resume: ResumeData, jd: JobDescriptionData) -> Dict[str, Any]:
    """
    Compares candidate education history against JD required and preferred education.
    Calculates compatibility and matches degrees/majors.
    """
    logger.info("Analyzing education credentials.")
    
    edu_list = resume.education
    if not edu_list:
        # If no education list, score is 0 unless JD has no education requirements
        has_reqs = len(jd.required_education) > 0
        return {
            "highest_candidate_degree": "None",
            "highest_degree_rank": 0,
            "meets_education_requirement": not has_reqs,
            "education_match_score": 100.0 if not has_reqs else 0.0,
            "reasons": ["No education history found in resume."] if has_reqs else []
        }
        
    # Get candidate's highest degree level and major
    highest_rank = 0
    highest_degree = "Unknown"
    highest_major = ""
    
    for edu in edu_list:
        rank = get_degree_rank(edu.degree)
        if rank > highest_rank:
            highest_rank = rank
            highest_degree = normalize_degree(edu.degree)
            highest_major = edu.major or ""
            
    # Parse JD requirements
    # Get the highest degree required from the list (often just one required degree is listed, e.g. BS)
    required_rank = 0
    required_degrees = jd.required_education
    
    if required_degrees:
        for rd in required_degrees:
            rank = get_degree_rank(rd)
            if rank > required_rank:
                required_rank = rank
                
    # Evaluate degree rank compatibility
    meets_degree = highest_rank >= required_rank
    
    # Evaluate major compatibility (if JD lists specific majors or fields of study)
    # We can infer major requirements from nice-to-have or preferred_education
    jd_majors = []
    for pe in jd.preferred_education:
        # If preferred education includes major keywords
        if len(pe) > 3:
            jd_majors.append(pe)
            
    major_ok = match_major(highest_major, jd_majors)
    
    # Calculate score
    if required_rank == 0:
        # No requirement specified
        base_score = 100.0
    elif highest_rank >= required_rank:
        # Meets or exceeds
        base_score = 100.0
        # Give a small bonus if exceeds
        if highest_rank > required_rank:
            base_score = min(100.0, base_score + 5.0)
    elif highest_rank == required_rank - 1:
        # One level below (e.g. Master's required, has Bachelor's)
        base_score = 70.0
    else:
        # Significantly below
        base_score = 40.0
        
    # Apply major penalty if not matching
    if not major_ok:
        base_score = max(0.0, base_score - 15.0)
        
    reasons = []
    if not meets_degree and required_rank > 0:
        reasons.append(
            f"Highest degree ({highest_degree}) is below the required level ({normalize_degree(required_degrees[0])})."
        )
    if not major_ok and jd_majors:
        reasons.append(
            f"Candidate major ({highest_major}) does not align with requested majors: {', '.join(jd_majors)}."
        )
        
    return {
        "highest_candidate_degree": highest_degree,
        "highest_degree_rank": highest_rank,
        "meets_education_requirement": meets_degree,
        "education_match_score": round(base_score, 1),
        "reasons": reasons
    }
