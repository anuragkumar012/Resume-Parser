from typing import List, Optional
from pydantic import BaseModel, Field

class CandidateInfo(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number with country code if available")
    location: Optional[str] = Field(None, description="Current city/state/country")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    portfolio: Optional[str] = Field(None, description="Portfolio or personal website URL")
    total_experience_years: Optional[float] = Field(None, description="Total years of work experience, calculated or declared")
    current_company: Optional[str] = Field(None, description="Current employer company name")
    current_role: Optional[str] = Field(None, description="Current job title/role")
    notice_period_days: Optional[int] = Field(None, description="Notice period in days, if mentioned")
    current_ctc: Optional[str] = Field(None, description="Current CTC or salary details")
    expected_ctc: Optional[str] = Field(None, description="Expected CTC or salary requirements")
    work_authorization: Optional[str] = Field(None, description="Work authorization details (e.g. US Citizen, H1B, EU Citizen)")
    visa_status: Optional[str] = Field(None, description="Current visa status (e.g. H1B, OPT, F1)")
    preferred_location: Optional[str] = Field(None, description="Preferred job location")
    remote_preference: Optional[str] = Field(None, description="Remote work preference (Remote, Hybrid, Onsite)")

class Skills(BaseModel):
    primary_skills: List[str] = Field(default_factory=list, description="Core professional/technical skills")
    secondary_skills: List[str] = Field(default_factory=list, description="Secondary or supporting technical skills")
    tools: List[str] = Field(default_factory=list, description="Software tools used (e.g. Git, Slack, Jira)")
    frameworks: List[str] = Field(default_factory=list, description="Web/Application frameworks (e.g. React, Django, Spring)")
    programming_languages: List[str] = Field(default_factory=list, description="Programming languages (e.g. Python, C++, Java)")
    cloud_platforms: List[str] = Field(default_factory=list, description="Cloud platforms (e.g. AWS, GCP, Azure)")
    databases: List[str] = Field(default_factory=list, description="Databases (e.g. PostgreSQL, MongoDB, Redis)")
    soft_skills: List[str] = Field(default_factory=list, description="Soft skills (e.g. leadership, communication)")

class WorkExperience(BaseModel):
    company: str = Field(..., description="Name of the company/employer")
    role: str = Field(..., description="Job title or role held")
    duration: Optional[str] = Field(None, description="Duration string (e.g. '2 years', 'June 2021 - Present')")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM or YYYY-MM-DD format if parseable, or month/year text)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM or YYYY-MM-DD or 'Present' if current job)")
    responsibilities: List[str] = Field(default_factory=list, description="List of responsibilities or tasks performed")
    achievements: List[str] = Field(default_factory=list, description="Quantifiable achievements, metrics, or notable successes")
    projects: List[str] = Field(default_factory=list, description="Projects worked on within this company")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies/tools/languages used in this role")

class EducationDetail(BaseModel):
    institution: str = Field(..., description="Name of the university, college, or school")
    degree: str = Field(..., description="Degree type (e.g. Bachelor of Science, Master of Business Administration, B.Tech)")
    major: Optional[str] = Field(None, description="Field of study or major specialization")
    cgpa: Optional[str] = Field(None, description="GPA, grade percentage, or marks obtained")
    graduation_year: Optional[int] = Field(None, description="Year of graduation")

class CertificationDetail(BaseModel):
    name: str = Field(..., description="Name of the certification")
    issuing_authority: Optional[str] = Field(None, description="Organization that issued the certification")
    year: Optional[int] = Field(None, description="Year of issuance")

class PublicationDetail(BaseModel):
    title: str = Field(..., description="Title of the paper, article, or book")
    publisher: Optional[str] = Field(None, description="Journal, conference, or publisher name")
    year: Optional[int] = Field(None, description="Year of publication")
    url: Optional[str] = Field(None, description="Link to the publication")

class AwardDetail(BaseModel):
    name: str = Field(..., description="Name of the award/recognition")
    issuer: Optional[str] = Field(None, description="Organization issuing the award")
    year: Optional[int] = Field(None, description="Year awarded")

class ResumeData(BaseModel):
    candidate_info: CandidateInfo = Field(default_factory=CandidateInfo, description="Personal and contact information")
    skills: Skills = Field(default_factory=Skills, description="Categorized list of skills")
    work_experience: List[WorkExperience] = Field(default_factory=list, description="Chronological work history")
    education: List[EducationDetail] = Field(default_factory=list, description="Academic history")
    certifications: List[CertificationDetail] = Field(default_factory=list, description="Professional certifications")
    publications: List[PublicationDetail] = Field(default_factory=list, description="Scientific papers or articles")
    awards: List[AwardDetail] = Field(default_factory=list, description="Awards and recognitions")
    llm_usage: Optional[dict] = Field(None, description="LLM token and cost usage metadata")
