from typing import List, Dict, Tuple, Set, Any
from rapidfuzz import fuzz
from loguru import logger

from resume_ai.models.resume_schema import ResumeData, Skills
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.utils.normalizer import normalize_skill

# Predefined categories of emerging / trending tech skills for mapping
EMERGING_TECH_KEYWORDS = {
    "generative ai", "llm", "large language models", "prompt engineering", "langchain",
    "llamaindex", "copilot", "vector databases", "chromadb", "pinecone", "milvus",
    "rag", "bert", "gpt", "rlhf", "huggingface", "stable diffusion", "midjourney"
}

# Transferable skill clusters (e.g. if JD wants Django, Flask is highly transferable)
TRANSFERABLE_CLUSTERS = [
    {"django", "flask", "fastapi", "tornado", "bottle"},  # Python web
    {"react", "angular", "vue", "svelte", "ember"},       # Frontend JS
    {"express", "nest", "koa", "hapi"},                   # Node backend
    {"postgresql", "mysql", "mariadb", "sqlite"},          # Relational DB
    {"mongodb", "couchdb", "dynamodb", "firestore"},      # Document NoSQL
    {"redis", "memcached"},                               # Caching
    {"pytorch", "tensorflow", "keras", "mxnet", "jax"},    # DL Frameworks
    {"aws", "gcp", "azure", "oracle cloud", "digitalocean"}, # Cloud
    {"git", "github", "gitlab", "bitbucket"},             # VCS
]

def get_flat_resume_skills(skills_obj: Skills) -> List[str]:
    """Flattens all categorized skills from ResumeData into a single list."""
    flat = []
    flat.extend(skills_obj.primary_skills)
    flat.extend(skills_obj.secondary_skills)
    flat.extend(skills_obj.tools)
    flat.extend(skills_obj.frameworks)
    flat.extend(skills_obj.programming_languages)
    flat.extend(skills_obj.cloud_platforms)
    flat.extend(skills_obj.databases)
    flat.extend(skills_obj.soft_skills)
    
    # Filter empty strings and normalize
    return list({normalize_skill(s) for s in flat if s and s.strip()})

def match_skill_fuzzy(candidate_skill: str, target_skill: str, threshold: float = 85.0) -> bool:
    """Fuzzy matches two skills using RapidFuzz token sorting."""
    c_norm = normalize_skill(candidate_skill).lower()
    t_norm = normalize_skill(target_skill).lower()
    
    if c_norm == t_norm:
        return True
        
    # Check token sort ratio
    ratio = fuzz.token_sort_ratio(c_norm, t_norm)
    if ratio >= threshold:
        return True
        
    return False

def check_transferable(candidate_skills: Set[str], missing_skill: str) -> bool:
    """Checks if the candidate possesses a skill transferable to the missing one."""
    missing_lower = missing_skill.lower()
    for cluster in TRANSFERABLE_CLUSTERS:
        if missing_lower in cluster:
            # Check if candidate has ANY other skill in this cluster
            intersect = candidate_skills.intersection(cluster)
            # Remove the missing skill itself if candidate somehow has it
            intersect.discard(missing_lower)
            if intersect:
                return True
    return False

def analyze_skills(resume: ResumeData, jd: JobDescriptionData) -> Dict[str, Any]:
    """
    Compares candidate skills against job description required and preferred skills.
    Calculates match scores and identifies gaps, strong, weak, and transferable skills.
    """
    logger.info("Analyzing skill matches.")
    
    # Extract & normalize candidate skills
    candidate_skills = get_flat_resume_skills(resume.skills)
    candidate_skills_set = {s.lower() for s in candidate_skills}
    
    # JD Skills
    jd_req_skills = [normalize_skill(s) for s in jd.required_skills if s]
    jd_pref_skills = [normalize_skill(s) for s in jd.preferred_skills if s]
    
    matched_req: List[str] = []
    missing_req: List[str] = []
    
    matched_pref: List[str] = []
    missing_pref: List[str] = []
    
    strong_skills: List[str] = []
    weak_skills: List[str] = []
    transferable: List[str] = []
    
    # Match Required Skills
    for req in jd_req_skills:
        found = False
        for cand in candidate_skills:
            if match_skill_fuzzy(cand, req, threshold=85.0):
                matched_req.append(req)
                strong_skills.append(cand)
                found = True
                break
        if not found:
            missing_req.append(req)
            # Check if candidate has a transferable skill
            if check_transferable(candidate_skills_set, req):
                transferable.append(req)
                
    # Match Preferred Skills
    for pref in jd_pref_skills:
        found = False
        for cand in candidate_skills:
            if match_skill_fuzzy(cand, pref, threshold=85.0):
                matched_pref.append(pref)
                found = True
                break
        if not found:
            missing_pref.append(pref)
            
    # Classify candidate's remaining skills as emerging tech if matching
    emerging: List[str] = []
    for cand in candidate_skills:
        if cand.lower() in EMERGING_TECH_KEYWORDS:
            emerging.append(cand)
            
    # Identify Weak Skills
    # A skill is weak if matched fuzzy but score is borderline, or candidate lists it
    # in secondary but it is required, or if it is only mentioned without projects/experience references
    # Let's say: candidate has it in secondary skills but it is key in required skills.
    secondary_set = {normalize_skill(s).lower() for s in resume.skills.secondary_skills}
    for req in matched_req:
        if req.lower() in secondary_set:
            weak_skills.append(req)
            
    # Calculate skill match score
    # Formula: (matched_req / total_req) * 80 + (matched_pref / total_pref if present else 0) * 20
    total_req_count = len(jd_req_skills)
    total_pref_count = len(jd_pref_skills)
    
    req_score = 0.0
    pref_score = 0.0
    
    if total_req_count > 0:
        req_score = (len(matched_req) / total_req_count) * 100
    else:
        req_score = 100.0  # if no required skills listed
        
    if total_pref_count > 0:
        pref_score = (len(matched_pref) / total_pref_count) * 100
    else:
        pref_score = 100.0  # if no preferred skills listed
        
    # Combined score: 80% weight on required, 20% on preferred
    skill_match_score = (req_score * 0.8) + (pref_score * 0.2)
    
    # Deduplicate strong skills list
    strong_skills = list(set(strong_skills))
    weak_skills = list(set(weak_skills))
    
    # Filter weak skills out of strong skills
    strong_skills = [s for s in strong_skills if s not in weak_skills]
    
    return {
        "skill_match_score": round(skill_match_score, 1),
        "matched_required_skills": matched_req,
        "missing_required_skills": missing_req,
        "matched_preferred_skills": matched_pref,
        "missing_preferred_skills": missing_pref,
        "strong_skills": strong_skills,
        "weak_skills": weak_skills,
        "transferable_skills": transferable,
        "emerging_skills": emerging,
    }
