from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from resume_ai.database.db import Base

class JobDescriptionDB(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=True)
    raw_text = Column(LONGTEXT, nullable=True)
    parsed_json = Column(LONGTEXT, nullable=True)  # JSON dump of JobDescriptionData
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to match reports
    reports = relationship("MatchReportDB", back_populates="job", cascade="all, delete-orphan")

class CandidateDB(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    raw_resume_text = Column(LONGTEXT, nullable=True)
    parsed_json = Column(LONGTEXT, nullable=True)  # JSON dump of ResumeData
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship to match reports
    reports = relationship("MatchReportDB", back_populates="candidate", cascade="all, delete-orphan")

class MatchReportDB(Base):
    __tablename__ = "match_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    
    ats_score = Column(Float, nullable=True)
    semantic_score = Column(Float, nullable=True)
    skill_match = Column(Float, nullable=True)
    experience_match = Column(Float, nullable=True)
    education_match = Column(Float, nullable=True)
    keyword_match = Column(Float, nullable=True)
    eligibility = Column(String(50), nullable=True)
    eligibility_reasons = Column(Text, nullable=True)  # Comma separated or small JSON array
    full_report_json = Column(LONGTEXT, nullable=True)  # Full MatchReport JSON dump
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    job = relationship("JobDescriptionDB", back_populates="reports")
    candidate = relationship("CandidateDB", back_populates="reports")


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)  # Hashed (SHA-256)
    role = Column(String(50), nullable=False)       # "candidate" or "company"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
