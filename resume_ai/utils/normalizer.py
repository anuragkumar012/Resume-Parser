import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import dateparser
from loguru import logger

# Skill mappings (aliases)
SKILL_ALIASES: Dict[str, str] = {
    "python3": "Python",
    "python 3": "Python",
    "py": "Python",
    
    "reactjs": "React",
    "react.js": "React",
    "react js": "React",
    
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node": "Node.js",
    
    "aws ec2": "AWS EC2",
    "ec2": "AWS EC2",
    "amazon ec2": "AWS EC2",
    
    "aws s3": "AWS S3",
    "s3": "AWS S3",
    "amazon s3": "AWS S3",
    
    "typescript": "TypeScript",
    "ts": "TypeScript",
    
    "javascript": "JavaScript",
    "js": "JavaScript",
    
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    
    "docker": "Docker",
    
    "golang": "Go",
    "go language": "Go",
    
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    
    "scikit-learn": "Scikit-Learn",
    "sklearn": "Scikit-Learn",
    
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",
    
    "pytorch": "PyTorch",
}

# Degree level normalization
DEGREE_MAPPING: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\b(ph\.?d|doctorate|doctor of philosophy)\b", re.I), "Doctorate"),
    (re.compile(r"\b(m\.?s|m\.?sc|master of science|m\.?tech|mba|master of business administration|master)\b", re.I), "Master's Degree"),
    (re.compile(r"\b(b\.?s|b\.?sc|b\.?tech|b\.?e|bachelor of science|bachelor of engineering|bachelor of technology|bachelor)\b", re.I), "Bachelor's Degree"),
    (re.compile(r"\b(associate|assoc)\b", re.I), "Associate's Degree"),
    (re.compile(r"\b(high school|diploma|secondary school)\b", re.I), "High School Diploma"),
]

# Company suffix cleaning
COMPANY_SUFFIX_PAT = re.compile(
    r"\b(inc|ltd|llc|co|corp|corporation|incorporated|limited|gmbh|pvt|public limited)\b[.]?", 
    re.IGNORECASE
)

# Date normalization regexes for fast matching
DATE_PATTERNS = [
    re.compile(r"^(?P<month>\d{1,2})/(?P<year>\d{4})$"),
    re.compile(r"^(?P<month>[A-Za-z]+)\s*(?P<year>\d{4})$"),
    re.compile(r"^(?P<year>\d{4})$")
]

def normalize_skill(skill: str) -> str:
    """Standardizes skill aliases to a canonical name."""
    skill_clean = skill.strip().lower()
    if skill_clean in SKILL_ALIASES:
        return SKILL_ALIASES[skill_clean]
    # Check if string matches with minor formatting differences
    # We can also do exact title case for others
    # but return standard alias if exists
    return skill.strip()

def normalize_company(company: str) -> str:
    """Removes common corporate suffixes (Inc., LLC, Ltd., etc.) to standardize company name."""
    if not company:
        return ""
    comp = company.strip()
    # Strip suffix
    comp = COMPANY_SUFFIX_PAT.sub("", comp)
    # Clean up double spaces or trailing punctuation
    comp = re.sub(r"\s+", " ", comp)
    comp = comp.strip().rstrip(",.- ")
    return comp or company.strip()

def normalize_degree(degree: str) -> str:
    """Categorizes a raw degree text into standard buckets (Bachelor's, Master's, etc.)."""
    if not degree:
        return "Unknown"
    deg = degree.strip()
    for pattern, normalized in DEGREE_MAPPING:
        if pattern.search(deg):
            return normalized
    return deg

def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parses a fuzzy date string into a datetime object.
    Supports YYYY, MM/YYYY, Month YYYY, etc.
    """
    if not date_str or not isinstance(date_str, str):
        return None
        
    date_clean = date_str.strip().lower()
    if date_clean in ["present", "current", "now", "ongoing", "active"]:
        return datetime.now()
        
    # Fallback to dateparser for flexible date parsing
    try:
        parsed = dateparser.parse(
            date_str, 
            settings={"PREFER_DAY_OF_MONTH": "first", "STRICT_PARSING": False}
        )
        if parsed:
            return parsed
    except Exception as e:
        logger.debug(f"Dateparser failed to parse '{date_str}': {e}")
        
    return None

def normalize_date_to_string(date_str: Optional[str]) -> Optional[str]:
    """Converts a fuzzy date string into YYYY-MM format."""
    parsed = parse_date_string(date_str)
    if parsed:
        # Check if the text matches 'present'
        if date_str and date_str.strip().lower() in ["present", "current"]:
            return "Present"
        return parsed.strftime("%Y-%m")
    return date_str

def calculate_duration_months(start_date_str: Optional[str], end_date_str: Optional[str]) -> int:
    """Calculates the duration between two date strings in months."""
    start_dt = parse_date_string(start_date_str)
    end_dt = parse_date_string(end_date_str) or datetime.now()
    
    if not start_dt:
        return 0
        
    # Calculate difference in months
    diff = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    return max(0, diff)

def normalize_location(location: str) -> str:
    """Standardizes casing and cleans up spacing of locations."""
    if not location:
        return ""
    loc = location.strip()
    # Normalize common abbreviations
    loc = re.sub(r"\b(usa|u\.s\.a|united states of america)\b", "United States", loc, flags=re.IGNORECASE)
    loc = re.sub(r"\b(uk|u\.k|united kingdom)\b", "United Kingdom", loc, flags=re.IGNORECASE)
    # Capitalize each word nicely
    return " ".join([word.capitalize() for word in loc.split()])
