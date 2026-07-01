from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger

from resume_ai.models.resume_schema import ResumeData, WorkExperience
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.utils.normalizer import parse_date_string, calculate_duration_months

LEADERSHIP_KEYWORDS = {
    "lead", "leader", "managing", "manager", "director", "vp", "vice president", 
    "head", "chief", "cto", "cio", "ceo", "architect", "principal", "founder", 
    "co-founder", "scrum master", "supervisor"
}

def parse_work_intervals(experience_list: List[WorkExperience]) -> List[Tuple[datetime, datetime]]:
    """Parses experience list into a list of start and end datetime tuples."""
    intervals = []
    for exp in experience_list:
        start_dt = parse_date_string(exp.start_date)
        end_dt = parse_date_string(exp.end_date) or datetime.now()
        
        if start_dt:
            # Ensure start is before end
            if start_dt > end_dt:
                start_dt, end_dt = end_dt, start_dt
            intervals.append((start_dt, end_dt))
            
    return intervals

def merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
    """Merges overlapping date intervals to avoid double-counting experience."""
    if not intervals:
        return []
        
    # Sort intervals by start date
    sorted_intervals = sorted(intervals, key=lambda x: x[0])
    merged = [sorted_intervals[0]]
    
    for current_start, current_end in sorted_intervals[1:]:
        last_start, last_end = merged[-1]
        
        # If current interval overlaps with the last merged interval
        if current_start <= last_end:
            # Merge them by extending the end date if necessary
            merged[-1] = (last_start, max(last_end, current_end))
        else:
            merged.append((current_start, current_end))
            
    return merged

def calculate_years_from_intervals(intervals: List[Tuple[datetime, datetime]]) -> float:
    """Calculates total years from a list of date intervals."""
    total_days = 0
    for start, end in intervals:
        total_days += (end - start).days
    return round(total_days / 365.25, 1)

def analyze_experience(resume: ResumeData, jd: JobDescriptionData) -> Dict[str, Any]:
    """
    Analyzes candidate work history: total experience, relevance, gaps, and job change frequency.
    """
    logger.info("Analyzing work experience.")
    
    exp_list = resume.work_experience
    if not exp_list:
        return {
            "total_experience_years": 0.0,
            "relevant_experience_years": 0.0,
            "leadership_experience_years": 0.0,
            "domain_experience_years": 0.0,
            "average_job_duration_months": 0.0,
            "employment_gaps": [],
            "frequent_job_changes": False,
            "experience_match_score": 0.0
        }
        
    # Parse intervals
    intervals = parse_work_intervals(exp_list)
    merged = merge_intervals(intervals)
    
    # 1. Total Experience
    total_exp_years = calculate_years_from_intervals(merged)
    
    # 2. Relevant Experience, Leadership, and Domain Experience
    # We will score each job individually for relevance
    relevant_intervals = []
    leadership_intervals = []
    domain_intervals = []
    
    jd_title_words = {w.lower() for w in (jd.title or "").split() if len(w) > 2}
    jd_domain = (jd.domain or "").lower()
    jd_industry = (jd.industry or "").lower()
    
    for exp in exp_list:
        start_dt = parse_date_string(exp.start_date)
        end_dt = parse_date_string(exp.end_date) or datetime.now()
        if not start_dt:
            continue
            
        role_lower = exp.role.lower()
        company_lower = exp.company.lower()
        
        # Check relevance:
        # If role matches some title words, or if there is substantial skill alignment
        is_relevant = False
        if any(word in role_lower for word in jd_title_words):
            is_relevant = True
        else:
            # check intersection of job tech stack with JD required skills
            tech_lower = {t.lower() for t in exp.tech_stack}
            jd_req_lower = {s.lower() for s in jd.required_skills}
            overlap = tech_lower.intersection(jd_req_lower)
            if len(overlap) >= 2 or (len(jd_req_lower) > 0 and len(overlap) / len(jd_req_lower) >= 0.25):
                is_relevant = True
                
        if is_relevant:
            relevant_intervals.append((start_dt, end_dt))
            
        # Check leadership:
        if any(keyword in role_lower for keyword in LEADERSHIP_KEYWORDS):
            leadership_intervals.append((start_dt, end_dt))
            
        # Check domain/industry:
        if jd_domain and (jd_domain in role_lower or any(jd_domain in resp.lower() for resp in exp.responsibilities)):
            domain_intervals.append((start_dt, end_dt))
        elif jd_industry and (jd_industry in company_lower or jd_industry in role_lower):
            domain_intervals.append((start_dt, end_dt))
            
    # Merge and calculate years
    relevant_exp_years = calculate_years_from_intervals(merge_intervals(relevant_intervals))
    leadership_exp_years = calculate_years_from_intervals(merge_intervals(leadership_intervals))
    domain_exp_years = calculate_years_from_intervals(merge_intervals(domain_intervals))
    
    # 3. Average Job Duration (months)
    durations = [calculate_duration_months(exp.start_date, exp.end_date) for exp in exp_list]
    avg_job_duration = round(sum(durations) / len(durations), 1) if durations else 0.0
    
    # 4. Employment Gaps
    # We find gaps between merged intervals
    gaps: List[str] = []
    sorted_merged = sorted(merged, key=lambda x: x[0])
    
    for i in range(len(sorted_merged) - 1):
        end_current = sorted_merged[i][1]
        start_next = sorted_merged[i+1][0]
        
        if start_next > end_current:
            diff_days = (start_next - end_current).days
            if diff_days > 90:  # gap of more than ~3 months
                gap_months = round(diff_days / 30.43, 1)
                gaps.append(
                    f"Gap of {gap_months} months between {end_current.strftime('%b %Y')} and {start_next.strftime('%b %Y')}"
                )
                
    # 5. Job Hopping Detection
    # If candidate had more than 2 jobs of duration < 12 months in the last 5 years
    recent_short_jobs = 0
    five_years_ago = datetime.now() - timedelta(days=5*365)
    
    for exp in exp_list:
        start_dt = parse_date_string(exp.start_date)
        if start_dt and start_dt >= five_years_ago:
            dur = calculate_duration_months(exp.start_date, exp.end_date)
            if dur < 12:
                recent_short_jobs += 1
                
    frequent_job_changes = recent_short_jobs >= 2
    
    # 6. Experience Match Score (0 - 100)
    # Based on required years of experience in JD
    min_years = jd.min_experience_years or 0.0
    
    if min_years == 0:
        exp_match_score = 100.0
    else:
        # Ratio of relevant experience to required min experience, capped at 100
        # If total experience is also low, penalize
        ratio = relevant_exp_years / min_years
        if ratio >= 1.0:
            exp_match_score = 100.0
        else:
            # Let total experience lift the score slightly (e.g. if they have 5 years total but only 2 relevant for a 3-year requirement)
            total_ratio = total_exp_years / min_years
            exp_match_score = (ratio * 0.8 + min(1.0, total_ratio) * 0.2) * 100.0
            
    # Penalize for job hopping or long unexplained gaps
    if frequent_job_changes:
        exp_match_score = max(0.0, exp_match_score - 10.0)
    if len(gaps) >= 3:
        exp_match_score = max(0.0, exp_match_score - 5.0)
        
    return {
        "total_experience_years": total_exp_years,
        "relevant_experience_years": relevant_exp_years,
        "leadership_experience_years": leadership_exp_years,
        "domain_experience_years": domain_exp_years,
        "average_job_duration_months": avg_job_duration,
        "employment_gaps": gaps,
        "frequent_job_changes": frequent_job_changes,
        "experience_match_score": round(exp_match_score, 1)
    }
