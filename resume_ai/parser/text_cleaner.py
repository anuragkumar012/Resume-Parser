import re
import unicodedata
from typing import Optional, List, Dict

def clean_text(text: str) -> str:
    """
    Cleans raw text extracted from PDF.
    Standardizes whitespace, bullet points, normalizes Unicode characters,
    and removes common PDF conversion artifacts.
    """
    if not text:
        return ""

    # Normalize Unicode characters (NFC form)
    text = unicodedata.normalize("NFC", text)

    # Standardize common ligatures and special characters
    replacements = {
        "\uf0b7": "-",  # common bullet char
        "\u2022": "-",  # bullet point
        "\u2023": "-",  # triangular bullet
        "\u2043": "-",  # hyphen bullet
        "\u2013": "-",  # en dash
        "\u2014": "-",  # em dash
        "\u2212": "-",  # minus sign
        "\u201c": '"',  # left double quote
        "\u201d": '"',  # right double quote
        "\u2018": "'",  # left single quote
        "\u2019": "'",  # right single quote
        "\xa0": " ",    # non-breaking space
        "\t": " ",      # tabs
    }
    
    for key, val in replacements.items():
        text = text.replace(key, val)

    # Remove non-printable control characters, but keep newlines
    text = "".join(ch for ch in text if ch == "\n" or ch == "\r" or unicodedata.category(ch)[0] != "C")

    # Replace multiple spaces with a single space (preserving newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Clean consecutive newlines (max 2 consecutive newlines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Strip whitespace from margins of lines
    cleaned_lines = [line.strip() for line in text.splitlines()]
    
    # Filter empty lines if there are too many, but keep structure
    text = "\n".join(cleaned_lines)
    
    # Final strip
    return text.strip()

def strip_markdown(text: str) -> str:
    """Removes markdown code blocks if the LLM output is wrapped in ```json ... ```."""
    if not text:
        return ""
    text = text.strip()
    if text.startswith("```"):
        # Remove first line
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def clean_jd_boilerplate(text: str) -> str:
    """
    Strips standard non-skill sections (benefits, EEO clauses, perks, how to apply)
    towards the end of the Job Description to save token usage.
    """
    if not text:
        return ""
        
    cleaned = clean_text(text)
    lines = cleaned.split("\n")
    n = len(lines)
    cutoff = int(n * 0.6) # look only in the last 40% of the description
    
    # regex for common boilerplate headings
    boilerplate_headers = [
        r"^\s*(what we offer|benefits|perks|our benefits|compensation|salary range|equal opportunity|about the company|about us|diversity|inclusion|how to apply|application instructions|eeo)\b"
    ]
    
    for i in range(cutoff, n):
        line = lines[i].strip().lower()
        for pattern in boilerplate_headers:
            if re.search(pattern, line):
                # Truncate here
                return "\n".join(lines[:i]).strip()
                
    return cleaned
