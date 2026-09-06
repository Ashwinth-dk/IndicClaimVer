import re
import unicodedata
from typing import Optional

def normalize_indic_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes text while strictly preserving Indic scripts,
    Unicode characters, accents, and meaningful punctuation.
    
    - Strips control characters without destroying Indic combining marks/matras.
    - Normalizes Unicode representations (NFC).
    - Normalizes multiple spaces, tabs, and newline sequences.
    - Does NOT convert to ASCII and does NOT strip Indic characters.
    """
    if not text:
        return ""
    
    # 1. Normalize Unicode (NFC forms composed characters correctly for Indic scripts)
    normalized = unicodedata.normalize("NFC", text)
    
    # 2. Replace multiple newlines or tabs with standard spacing
    normalized = re.sub(r"[\r\n\t]+", " ", normalized)
    
    # 3. Normalize multiple whitespace characters into single space
    normalized = re.sub(r"\s+", " ", normalized)
    
    # 4. Remove unwanted non-printable control characters except standard punctuation & Unicode
    # Keep characters whose Unicode category is not Cc (Control)
    cleaned_chars = [
        char for char in normalized
        if unicodedata.category(char) != "Cc"
    ]
    cleaned = "".join(cleaned_chars)
    
    return cleaned.strip()

def preprocess_claim(claim: str) -> str:
    """Preprocesses user input claim."""
    return normalize_indic_text(claim)

def preprocess_evidence(evidence: str) -> str:
    """Preprocesses evidence passage text."""
    return normalize_indic_text(evidence)
