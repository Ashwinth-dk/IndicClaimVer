import re
import unicodedata
from typing import Optional

def normalize_indic_text(text: Optional[str]) -> str:
    """
    Cleans and normalizes text while strictly preserving Indic scripts (Tamil, Hindi, Marathi),
    Unicode characters, accents, and meaningful Indic punctuation (such as danda । and double danda ॥).
    
    - Normalizes Unicode representations to NFC (Canonical Composition).
    - Normalizes excessive whitespace and newlines while keeping paragraph breaks clean.
    - Strips non-printable control characters without damaging Indic combining marks/matras/viramas.
    - Never strips non-ASCII / Indian script characters.
    """
    if text is None:
        return ""
    
    text_str = str(text)
    if not text_str.strip():
        return ""
    
    # 1. Normalize Unicode (NFC forms composed characters correctly for Indic scripts)
    normalized = unicodedata.normalize("NFC", text_str)
    
    # 2. Replace control characters (except tab and newline) with space
    cleaned_chars = []
    for char in normalized:
        cat = unicodedata.category(char)
        if cat == "Cc" and char not in ("\n", "\r", "\t"):
            cleaned_chars.append(" ")
        else:
            cleaned_chars.append(char)
    cleaned = "".join(cleaned_chars)
    
    # 3. Replace multiple spaces/tabs into a single space
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\r\n|\r", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    return cleaned.strip()

def preprocess_claim(claim: Optional[str]) -> str:
    """Preprocesses claim text preserving raw Unicode and Indic script characters."""
    if not claim:
        return ""
    norm = normalize_indic_text(claim)
    # Remove outer surrounding quotes
    norm = re.sub(r'^["\'“‘]+|["\'”’]+$', '', norm.strip())
    return norm.strip()

def preprocess_evidence(evidence: Optional[str]) -> str:
    """Preprocesses evidence passage text preserving raw Unicode."""
    if not evidence:
        return ""
    return normalize_indic_text(evidence)

