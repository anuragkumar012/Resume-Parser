from typing import List, Optional
from pydantic import BaseModel, Field

class JobDescriptionData(BaseModel):
    title: Optional[str] = Field(None, description="Job title")
    company: Optional[str] = Field(None, description="Company name")
    required_skills: List[str] = Field(default_factory=list, description="Must-have technical or soft skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Nice-to-have or optional skills")
    min_experience_years: Optional[float] = Field(None, description="Minimum years of experience required")
    preferred_experience_years: Optional[float] = Field(None, description="Preferred or ideal years of experience")
    required_education: List[str] = Field(default_factory=list, description="Minimum degree or education credentials required (e.g. BS, MS, PhD)")
    preferred_education: List[str] = Field(default_factory=list, description="Preferred degrees or specializations")
    responsibilities: List[str] = Field(default_factory=list, description="Key duties and job responsibilities")
    location: Optional[str] = Field(None, description="Job location requirements")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, Internship, etc.")
    industry: Optional[str] = Field(None, description="Industry sector (e.g. Fintech, Healthcare, SaaS)")
    domain: Optional[str] = Field(None, description="Functional domain (e.g. Web Development, AI/ML, DevOps)")
    keywords: List[str] = Field(default_factory=list, description="Important terminology, buzzwords, or tools mentioned in the JD")
    mandatory_requirements: List[str] = Field(default_factory=list, description="Strict filter criteria (e.g. US Citizen, specific certifications)")
    nice_to_have: List[str] = Field(default_factory=list, description="Additional preferred qualifications or benefits")
    llm_usage: Optional[dict] = Field(None, description="LLM token and cost usage metadata")
