import re
from typing import Dict, List, Tuple
from loguru import logger

# Map standard section categories to regex patterns matching headers
SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(summary|professional summary|summary of qualifications|career objective|objective|about me|profile|personal statement)$",
        re.IGNORECASE
    ),
    "skills": re.compile(
        r"^(skills|technical skills|key skills|core competencies|skills & technologies|areas of expertise|technologies|tools|languages & tools)$",
        re.IGNORECASE
    ),
    "experience": re.compile(
        r"^(experience|work experience|professional experience|employment history|work history|professional background|career history)$",
        re.IGNORECASE
    ),
    "projects": re.compile(
        r"^(projects|key projects|academic projects|personal projects|technical projects|selected projects)$",
        re.IGNORECASE
    ),
    "education": re.compile(
        r"^(education|academic background|academic qualifications|educational qualifications|education history|academic profile)$",
        re.IGNORECASE
    ),
    "certifications": re.compile(
        r"^(certifications|licenses & certifications|credentials|professional certifications|certifications & courses)$",
        re.IGNORECASE
    ),
    "achievements": re.compile(
        r"^(achievements|awards|honors|awards & achievements|accomplishments|professional achievements)$",
        re.IGNORECASE
    ),
    "languages": re.compile(
        r"^(languages|languages known|language proficiency|spoken languages)$",
        re.IGNORECASE
    ),
    "publications": re.compile(
        r"^(publications|research papers|patents|selected publications|scientific publications)$",
        re.IGNORECASE
    ),
    "links": re.compile(
        r"^(links|online profiles|social profiles|contact|websites|portfolio & links)$",
        re.IGNORECASE
    )
}

def detect_sections(text: str) -> Dict[str, str]:
    """
    Scans the clean text and partitions it into structured sections.
    Returns a dictionary of section_name -> content block.
    """
    if not text:
        return {}

    lines = text.split("\n")
    sections: Dict[str, List[str]] = {}
    current_section = "header"  # text before any explicit section header
    sections[current_section] = []

    # Keep track of line numbers and content to check for section headers
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            # Preserve empty line if we have an active section
            if sections[current_section]:
                sections[current_section].append(line)
            continue

        # Check if this line matches any section header pattern
        # Headers are usually short (under 50 chars) and standalone
        matched_section = None
        if len(stripped_line) < 50:
            # Remove trailing colons, numbers, or symbols for matching
            normalized_header = re.sub(r"[:\-\d\s\u2022]+$", "", stripped_line).strip()
            
            for section_name, pattern in SECTION_PATTERNS.items():
                if pattern.match(normalized_header):
                    matched_section = section_name
                    break

        if matched_section:
            # Switch to new section
            logger.debug(f"Detected section: {matched_section} from header '{stripped_line}'")
            current_section = matched_section
            if current_section not in sections:
                sections[current_section] = []
        else:
            # Add line to current section
            sections[current_section].append(line)

    # Join lines for each section and return
    result: Dict[str, str] = {}
    for sec_name, sec_lines in sections.items():
        joined = "\n".join(sec_lines).strip()
        if joined:
            result[sec_name] = joined

    return result
