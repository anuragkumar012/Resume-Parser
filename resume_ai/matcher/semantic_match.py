from typing import Dict, Any, List
from loguru import logger

from resume_ai.models.resume_schema import ResumeData
from resume_ai.models.jd_schema import JobDescriptionData
from resume_ai.matcher.embeddings import get_embeddings, cosine_similarity

def build_resume_text_blocks(resume: ResumeData) -> Dict[str, str]:
    """Serializes various sections of the resume into text blocks for embedding generation."""
    # 1. Skills Text
    skills_list = []
    skills_list.extend(resume.skills.primary_skills)
    skills_list.extend(resume.skills.secondary_skills)
    skills_list.extend(resume.skills.frameworks)
    skills_list.extend(resume.skills.programming_languages)
    skills_list.extend(resume.skills.tools)
    skills_list.extend(resume.skills.cloud_platforms)
    skills_list.extend(resume.skills.databases)
    skills_text = ", ".join(skills_list)
    
    # 2. Experience Text
    exp_blocks = []
    for exp in resume.work_experience:
        exp_blocks.append(
            f"Role: {exp.role} at {exp.company}. "
            f"Responsibilities: {' '.join(exp.responsibilities)}. "
            f"Achievements: {' '.join(exp.achievements)}. "
            f"Technologies: {', '.join(exp.tech_stack)}."
        )
    exp_text = "\n".join(exp_blocks)
    
    # 3. Projects Text
    project_blocks = []
    for exp in resume.work_experience:
        if exp.projects:
            project_blocks.append(f"Company Projects: {' '.join(exp.projects)}")
    project_text = "\n".join(project_blocks)
    
    # 4. Education Text
    edu_blocks = []
    for edu in resume.education:
        edu_blocks.append(f"Degree: {edu.degree} in {edu.major} from {edu.institution}.")
    edu_text = "\n".join(edu_blocks)
    
    # 5. Full Profile Text
    full_text = f"{resume.candidate_info.current_role or ''} profile. Skills: {skills_text}. Experience: {exp_text}. Education: {edu_text}"
    
    return {
        "skills": skills_text.strip(),
        "experience": exp_text.strip(),
        "projects": project_text.strip(),
        "education": edu_text.strip(),
        "full_profile": full_text.strip()
    }

def build_jd_text_blocks(jd: JobDescriptionData) -> Dict[str, str]:
    """Serializes various sections of the job description into text blocks for embedding generation."""
    # 1. Skills Text
    skills_text = ", ".join(jd.required_skills + jd.preferred_skills)
    
    # 2. Responsibilities Text
    resp_text = "\n".join(jd.responsibilities)
    
    # 3. Projects/Nice to have Text
    proj_text = "\n".join(jd.nice_to_have) if jd.nice_to_have else "\n".join(jd.responsibilities)
    
    # 4. Education Text
    edu_text = ", ".join(jd.required_education + jd.preferred_education)
    
    # 5. Full Job description Text
    full_text = f"Job Title: {jd.title or ''}. Industry: {jd.industry or ''}. Domain: {jd.domain or ''}. Responsibilities: {resp_text}. Required Skills: {skills_text}."
    
    return {
        "skills": skills_text.strip(),
        "experience": resp_text.strip(),
        "projects": proj_text.strip(),
        "education": edu_text.strip(),
        "full_jd": full_text.strip()
    }

def calculate_semantic_matching(resume: ResumeData, jd: JobDescriptionData) -> Dict[str, float]:
    """
    Computes semantic cosine similarity scores between corresponding sections
    of the Resume and Job Description.
    """
    logger.info("Computing semantic section similarities.")
    
    r_blocks = build_resume_text_blocks(resume)
    j_blocks = build_jd_text_blocks(jd)
    
    # Define mapping of sections to compare
    comparison_pairs = [
        ("overall", r_blocks["full_profile"], j_blocks["full_jd"]),
        ("skills", r_blocks["skills"], j_blocks["skills"]),
        ("experience", r_blocks["experience"], j_blocks["experience"]),
        ("projects", r_blocks["projects"], j_blocks["projects"]),
        ("education", r_blocks["education"], j_blocks["education"]),
    ]
    
    # Filter empty blocks to avoid zero vector division errors
    valid_pairs = []
    texts_to_embed = []
    
    for key, r_txt, j_txt in comparison_pairs:
        if r_txt and j_txt:
            valid_pairs.append((key, len(texts_to_embed), len(texts_to_embed) + 1))
            texts_to_embed.extend([r_txt, j_txt])
            
    if not texts_to_embed:
        return {
            "overall_similarity": 0.0,
            "skills_similarity": 0.0,
            "experience_similarity": 0.0,
            "projects_similarity": 0.0,
            "education_similarity": 0.0,
        }
        
    # Generate all embeddings in a batch
    embeddings = get_embeddings(texts_to_embed)
    
    scores: Dict[str, float] = {
        "overall": 0.0,
        "skills": 0.0,
        "experience": 0.0,
        "projects": 0.0,
        "education": 0.0,
    }
    
    for key, r_idx, j_idx in valid_pairs:
        sim = cosine_similarity(embeddings[r_idx], embeddings[j_idx])
        # Convert -1..1 range to 0..100 percentage
        sim_pct = round(max(0.0, sim) * 100.0, 1)
        scores[key] = sim_pct
        
    return {
        "overall_similarity": scores["overall"],
        "skills_similarity": scores["skills"],
        "experience_similarity": scores["experience"],
        "projects_similarity": scores["projects"],
        "education_similarity": scores["education"],
    }
