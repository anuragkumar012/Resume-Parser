import pytest
from datetime import datetime
from unittest.mock import MagicMock

# Models
from resume_ai.models.resume_schema import ResumeData, Skills, CandidateInfo, WorkExperience, EducationDetail, CertificationDetail
from resume_ai.models.jd_schema import JobDescriptionData

# Normalizer
from resume_ai.utils.normalizer import (
    normalize_skill,
    normalize_company,
    normalize_degree,
    parse_date_string,
    normalize_date_to_string,
    calculate_duration_months
)

# Text Cleaner & Section Detector
from resume_ai.parser.text_cleaner import clean_text, strip_markdown
from resume_ai.parser.section_detector import detect_sections

# Matcher Engines
from resume_ai.matcher.skill_match import analyze_skills, match_skill_fuzzy
from resume_ai.matcher.experience_match import analyze_experience, merge_intervals, calculate_years_from_intervals
from resume_ai.matcher.education_match import analyze_education, get_degree_rank
from resume_ai.matcher.eligibility import check_eligibility
from resume_ai.matcher.ats_score import compute_ats_score

# =====================================================================
# 1. TEST TEXT CLEANER & SECTION DETECTOR
# =====================================================================

def test_clean_text():
    raw_input = "Hello \xa0 World! \uf0b7 Bullet point.\n\n\nNew line here.   "
    expected = "Hello World! - Bullet point.\n\nNew line here."
    assert clean_text(raw_input) == expected

def test_strip_markdown():
    md = "```json\n{\n  \"name\": \"Alice\"\n}\n```"
    expected = "{\n  \"name\": \"Alice\"\n}"
    assert strip_markdown(md) == expected

def test_detect_sections():
    text = (
        "Summary\n"
        "Experienced software developer.\n"
        "Work Experience\n"
        "Python Engineer at Google\n"
        "Education\n"
        "B.S. Computer Science"
    )
    sections = detect_sections(text)
    assert "summary" in sections
    assert "experience" in sections
    assert "education" in sections
    assert "Experienced software developer." in sections["summary"]

# =====================================================================
# 2. TEST DATA NORMALIZATIONS
# =====================================================================

def test_normalize_skill():
    assert normalize_skill("python3") == "Python"
    assert normalize_skill("react.js") == "React"
    assert normalize_skill("AWS EC2") == "AWS EC2"
    assert normalize_skill("Custom Skill") == "Custom Skill"

def test_normalize_company():
    assert normalize_company("Google LLC") == "Google"
    assert normalize_company("Microsoft Corporation") == "Microsoft"
    assert normalize_company("InnovateTech Inc.") == "InnovateTech"

def test_normalize_degree():
    assert normalize_degree("Bachelor of Science") == "Bachelor's Degree"
    assert normalize_degree("B.Tech in CS") == "Bachelor's Degree"
    assert normalize_degree("MBA") == "Master's Degree"
    assert normalize_degree("Ph.D") == "Doctorate"
    assert normalize_degree("Self-Taught") == "Self-Taught"

def test_parse_date_string():
    dt = parse_date_string("Present")
    assert dt is not None
    assert (datetime.now() - dt).seconds < 10 # very close to current time

    dt2 = parse_date_string("2021-06")
    assert dt2 is not None
    assert dt2.year == 2021
    assert dt2.month == 6

def test_calculate_duration_months():
    assert calculate_duration_months("2021-01", "2021-12") == 11
    assert calculate_duration_months("2021-01", "Present") >= 12

# =====================================================================
# 3. TEST MATCHER: SKILLS
# =====================================================================

def test_skill_match_fuzzy():
    assert match_skill_fuzzy("reactjs", "React") is True
    assert match_skill_fuzzy("kubernetes", "k8s") is False # requires mapping
    assert match_skill_fuzzy("Scikit-Learn", "sklearn") is False # requires mapping

def test_analyze_skills():
    resume = ResumeData(
        skills=Skills(
            primary_skills=["Python", "React", "Docker"],
            secondary_skills=["Git"],
            soft_skills=["Communication"]
        )
    )
    jd = JobDescriptionData(
        required_skills=["Python", "React", "Kubernetes"],
        preferred_skills=["Git", "Node.js"]
    )
    
    res = analyze_skills(resume, jd)
    assert res["skill_match_score"] > 0
    assert "Python" in res["matched_required_skills"]
    assert "React" in res["matched_required_skills"]
    assert "Kubernetes" in res["missing_required_skills"]
    assert "Git" in res["matched_preferred_skills"]
    assert "Node.js" in res["missing_preferred_skills"]

# =====================================================================
# 4. TEST MATCHER: EXPERIENCE
# =====================================================================

def test_merge_intervals():
    intervals = [
        (datetime(2020, 1, 1), datetime(2021, 1, 1)),
        (datetime(2020, 6, 1), datetime(2021, 6, 1)), # overlap
        (datetime(2022, 1, 1), datetime(2022, 12, 1)) # gap
    ]
    merged = merge_intervals(intervals)
    assert len(merged) == 2
    assert merged[0] == (datetime(2020, 1, 1), datetime(2021, 6, 1))
    assert merged[1] == (datetime(2022, 1, 1), datetime(2022, 12, 1))

def test_analyze_experience():
    resume = ResumeData(
        work_experience=[
            WorkExperience(
                company="Google",
                role="Senior Software Engineer",
                start_date="2021-06",
                end_date="Present",
                responsibilities=["Leading team, writing Python code."],
                tech_stack=["Python", "Docker"]
            ),
            WorkExperience(
                company="Startup Inc",
                role="Python Developer",
                start_date="2019-01",
                end_date="2021-05",
                responsibilities=["Developer duties."],
                tech_stack=["Python", "Django"]
            )
        ]
    )
    jd = JobDescriptionData(
        title="Senior Python Developer",
        min_experience_years=5.0,
        required_skills=["Python"]
    )
    
    res = analyze_experience(resume, jd)
    assert res["total_experience_years"] >= 5.0
    assert res["relevant_experience_years"] >= 5.0
    assert res["leadership_experience_years"] >= 4.0 # contains 'Senior' and 'team'
    assert res["experience_match_score"] == 100.0

# =====================================================================
# 5. TEST MATCHER: EDUCATION
# =====================================================================

def test_get_degree_rank():
    assert get_degree_rank("Bachelor of Science") == 3
    assert get_degree_rank("MBA") == 4
    assert get_degree_rank("High School") == 1

def test_analyze_education():
    resume = ResumeData(
        education=[
            EducationDetail(
                institution="MIT",
                degree="Master of Science",
                major="Computer Science",
                graduation_year=2020
            )
        ]
    )
    jd = JobDescriptionData(
        required_education=["BS Computer Science"]
    )
    
    res = analyze_education(resume, jd)
    assert res["meets_education_requirement"] is True
    assert res["education_match_score"] >= 100.0
    
    # Mismatch check
    jd2 = JobDescriptionData(
        required_education=["PhD Computer Science"]
    )
    res2 = analyze_education(resume, jd2)
    assert res2["meets_education_requirement"] is False
    assert res2["education_match_score"] < 100.0

# =====================================================================
# 6. TEST MATCHER: ELIGIBILITY & ATS SCORE
# =====================================================================

def test_check_eligibility():
    resume = ResumeData(
        candidate_info=CandidateInfo(
            visa_status="H1B",
            work_authorization="Needs Sponsorship",
            notice_period_days=30
        ),
        skills=Skills(primary_skills=["Python"])
    )
    # JD requires citizen or no sponsorship
    jd = JobDescriptionData(
        mandatory_requirements=["Must be US Citizen"]
    )
    
    skill_res = {"missing_required_skills": [], "matched_required_skills": ["Python"], "weak_skills": []}
    exp_res = {"relevant_experience_years": 5.0, "total_experience_years": 5.0}
    edu_res = {"meets_education_requirement": True, "highest_degree_rank": 3}
    
    elig = check_eligibility(resume, jd, skill_res, exp_res, edu_res)
    assert elig["eligibility"] == "Not Eligible"
    assert any("Visa status" in r for r in elig["eligibility_reasons"])

def test_compute_ats_score():
    resume = ResumeData(
        candidate_info=CandidateInfo(name="Alice", email="alice@test.com"),
        skills=Skills(soft_skills=["Communication"]),
        certifications=[CertificationDetail(name="AWS Solutions Architect")]
    )
    jd = JobDescriptionData(
        keywords=["AWS", "FastAPI"],
        required_skills=["Python"]
    )
    
    skill_res = {"skill_match_score": 80.0, "strong_skills": ["Python"], "weak_skills": []}
    exp_res = {"experience_match_score": 90.0, "total_experience_years": 6.0}
    edu_res = {"education_match_score": 100.0}
    semantic_sims = {"projects_similarity": 70.0}
    
    score_res = compute_ats_score(
        resume,
        jd,
        "Alice profile. Has Python, AWS Solutions Architect, FastAPI. Strong Communication.",
        skill_res,
        exp_res,
        edu_res,
        semantic_sims
    )
    
    assert score_res.overall_score > 0
    assert score_res.confidence >= 0.8
