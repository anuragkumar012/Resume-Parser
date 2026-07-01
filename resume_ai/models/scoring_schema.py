from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData

class CategoryScores(BaseModel):
    skills_score: float = Field(0.0, description="Score for skill match (0-100)")
    experience_score: float = Field(0.0, description="Score for experience match (0-100)")
    projects_score: float = Field(0.0, description="Score for project/tech stack match (0-100)")
    education_score: float = Field(0.0, description="Score for education match (0-100)")
    certifications_score: float = Field(0.0, description="Score for certifications match (0-100)")
    keywords_score: float = Field(0.0, description="Score for keyword density match (0-100)")
    soft_skills_score: float = Field(0.0, description="Score for soft skills match (0-100)")

class ATSScoreResult(BaseModel):
    overall_score: float = Field(0.0, description="Weighted ATS score (0-100)")
    category_scores: CategoryScores = Field(default_factory=CategoryScores)
    confidence: float = Field(0.0, description="Confidence in scoring assessment (0-1)")

class EligibilityResult(BaseModel):
    status: str = Field(..., description="Eligible, Partially Eligible, or Not Eligible")
    reasons: List[str] = Field(default_factory=list, description="Reasoning and logic behind the status classification")

class SkillGapResult(BaseModel):
    missing_skills: List[str] = Field(default_factory=list, description="Skills present in JD but missing in Resume")
    weak_skills: List[str] = Field(default_factory=list, description="Skills mentioned weakly or with very little experience")
    strong_skills: List[str] = Field(default_factory=list, description="Skills where the candidate demonstrates high proficiency")
    transferable_skills: List[str] = Field(default_factory=list, description="Skills that translate well from other domains/roles")
    emerging_skills: List[str] = Field(default_factory=list, description="Trending technologies mentioned by candidate")

class JobChangeDetail(BaseModel):
    company: str
    duration_months: int
    reason: Optional[str] = None

class ExperienceAnalysisResult(BaseModel):
    total_experience_years: float = Field(0.0, description="Parsed total years of experience")
    relevant_experience_years: float = Field(0.0, description="Years of experience relevant to the target JD")
    leadership_experience_years: float = Field(0.0, description="Years in leadership, management, or lead roles")
    domain_experience_years: float = Field(0.0, description="Years in this specific industry domain")
    average_job_duration_months: float = Field(0.0, description="Average duration of jobs held in months")
    employment_gaps: List[str] = Field(default_factory=list, description="Descriptions of any significant gaps between roles")
    frequent_job_changes: bool = Field(False, description="Whether the candidate displays job-hopping patterns")

class KeywordAnalysisResult(BaseModel):
    ats_keywords: List[str] = Field(default_factory=list, description="Identified keywords relevant for ATS scan")
    missing_keywords: List[str] = Field(default_factory=list, description="Key terms in JD that are missing in resume")
    keyword_density: Dict[str, float] = Field(default_factory=dict, description="Frequency percentage of key terms")
    important_phrases: List[str] = Field(default_factory=list, description="Crucial phrases extracted from resume")
    industry_terms: List[str] = Field(default_factory=list, description="Standard industry-specific abbreviations or terminology")

class ResumeQualityResult(BaseModel):
    grammar_issues: List[str] = Field(default_factory=list, description="Identified grammatical or writing errors")
    weak_action_verbs: List[str] = Field(default_factory=list, description="Action verbs that are generic (e.g. 'helped', 'worked on')")
    long_bullet_points: List[str] = Field(default_factory=list, description="Bullet points exceeding optimal character limits")
    passive_voice: List[str] = Field(default_factory=list, description="Instances of passive voice construction")
    formatting_problems: List[str] = Field(default_factory=list, description="Observations like uneven margins, font inconsistency")
    missing_contact_details: List[str] = Field(default_factory=list, description="Crucial contact links or details that are absent")
    missing_metrics: List[str] = Field(default_factory=list, description="Bullet points that lack quantifiable impact metrics")
    llm_usage: Optional[dict] = Field(None, description="LLM token and cost usage metadata")

class RecommendationItem(BaseModel):
    recommendation: str = Field(..., description="Actionable improvement text")
    priority: str = Field(..., description="High, Medium, or Low")
    section: str = Field(..., description="Target section of the resume (e.g. Experience, Skills, Contact)")

class MatchReport(BaseModel):
    id: Optional[int] = Field(None, description="Database ID of the match report")
    candidate_id: Optional[int] = Field(None, description="Database ID of the candidate")
    job_id: Optional[int] = Field(None, description="Database ID of the job description")
    candidate: ResumeData = Field(..., description="Structured resume representation")
    job: JobDescriptionData = Field(..., description="Structured job description representation")
    ats_score: float = Field(0.0, description="Composite ATS score (0-100)")
    semantic_score: float = Field(0.0, description="Overall semantic cosine similarity score (0-100)")
    skill_match: float = Field(0.0, description="Fuzzy and exact skill match score (0-100)")
    experience_match: float = Field(0.0, description="Experience alignment score (0-100)")
    education_match: float = Field(0.0, description="Education eligibility and level match score (0-100)")
    keyword_match: float = Field(0.0, description="Keyword overlap score (0-100)")
    eligibility: str = Field(..., description="Eligible, Partially Eligible, or Not Eligible")
    eligibility_reasons: List[str] = Field(default_factory=list, description="Explanations for eligibility classification")
    confidence: float = Field(0.0, description="System confidence coefficient (0.0 to 1.0)")
    missing_skills: List[str] = Field(default_factory=list, description="Primary missing skills list")
    resume_strengths: List[str] = Field(default_factory=list, description="Strengths identified in candidate profile")
    resume_weaknesses: List[str] = Field(default_factory=list, description="Weaknesses identified in candidate profile")
    recommendations: List[RecommendationItem] = Field(default_factory=list, description="Top prioritized improvements")
    skill_gap_analysis: Optional[SkillGapResult] = None
    experience_analysis: Optional[ExperienceAnalysisResult] = None
    keyword_analysis: Optional[KeywordAnalysisResult] = None
    quality_analysis: Optional[ResumeQualityResult] = None
    llm_usage: Optional[dict] = Field(None, description="Aggregated LLM token and cost usage metadata")
