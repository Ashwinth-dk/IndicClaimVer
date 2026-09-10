"""
Language Detection Utility for IndicClaim.
Accurately detects and validates English (en), Tamil (ta), Hindi (hi), and Marathi (mr).
Uses Unicode script boundary detection combined with lexical discriminant markers.
"""

import re
import unicodedata
from typing import Dict, Any, Tuple, Optional, Set

# Script Unicode Ranges
# Tamil: \u0B80 - \u0BFF
# Devanagari (Hindi & Marathi): \u0900 - \u097F
# Latin (English): ASCII / Latin-1 \u0000 - \u007F, \u0080 - \u00FF

TAMIL_PATTERN = re.compile(r'[\u0B80-\u0BFF]')
DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')
LATIN_PATTERN = re.compile(r'[a-zA-Z]')

# Marathi-specific unique characters and frequent morphemes/particles
# ळ (\u0933), ऱ (\u0931)
MARATHI_SPECIFIC_CHARS = re.compile(r'[\u0933\u0931]')

MARATHI_STOPWORDS: Set[str] = {
    "आहे", "आहेत", "होते", "होती", "झाला", "झाली", "झाले", "केले", "केली", "केला",
    "नाही", "नाहीत", "यांनी", "म्हणून", "करणार", "दिली", "दिला", "दिले", "सांगितले",
    "आणि", "पण", "परंतु", "किंवा", "तर", "त्या", "त्यांच्या", "यांच्या", "मध्ये",
    "वरील", "खालील", "केल्यानंतर", "झालेला", "असल्याचे", "यांना", "त्यांना", "अशी",
    "असा", "असे", "येथे", "तेथे", "कसा", "कशी", "कसे", "कोण", "कधी", "कुठे"
}

HINDI_STOPWORDS: Set[str] = {
    "है", "हैं", "था", "थी", "थे", "किया", "की", "के", "का", "को", "में", "पर",
    "नहीं", "और", "या", "लेकिन", "किंतु", "परंतु", "कहा", "बताया", "दिया", "हुए",
    "हुआ", "हुई", "होने", "करने", "होगा", "होगी", "होंगे", "इस", "उस", "यह",
    "वह", "इन", "उन", "किस", "किसे", "कैसे", "कहाँ", "कब", "क्यों", "सब", "भी",
    "तक", "ने", "से", "द्वारा", "बारे", "लिये", "लिए", "गया", "गई", "गए"
}

SUPPORTED_LANGUAGES = {"en": "English", "ta": "Tamil", "hi": "Hindi", "mr": "Marathi"}

class LanguageDetector:
    """
    High-precision, deterministic language detector for English, Tamil, Hindi, and Marathi.
    Handles raw text, titles, claims, and articles.
    """

    @classmethod
    def detect_language(cls, text: Optional[str]) -> Dict[str, Any]:
        """
        Detects language of given text.
        Returns: {
            "language": "en" | "ta" | "hi" | "mr" | "und",
            "language_name": str,
            "confidence": float (0.0 - 1.0),
            "script": "Tamil" | "Devanagari" | "Latin" | "Unknown",
            "details": Dict[str, Any]
        }
        """
        if not text or not str(text).strip():
            return {
                "language": "und",
                "language_name": "Undetermined",
                "confidence": 0.0,
                "script": "Unknown",
                "details": {"reason": "Empty text"}
            }

        clean_text = unicodedata.normalize("NFC", str(text)).strip()

        # Count character frequencies by script
        tamil_count = len(TAMIL_PATTERN.findall(clean_text))
        devanagari_count = len(DEVANAGARI_PATTERN.findall(clean_text))
        latin_count = len(LATIN_PATTERN.findall(clean_text))
        total_indic_or_latin = tamil_count + devanagari_count + latin_count

        if total_indic_or_latin == 0:
            return {
                "language": "und",
                "language_name": "Undetermined",
                "confidence": 0.0,
                "script": "Unknown",
                "details": {"reason": "No linguistic characters found"}
            }

        tamil_ratio = tamil_count / total_indic_or_latin
        devanagari_ratio = devanagari_count / total_indic_or_latin
        latin_ratio = latin_count / total_indic_or_latin

        # 1. Tamil Script check (Dominant Tamil characters)
        if tamil_ratio >= 0.40 or (tamil_count >= 5 and tamil_count > devanagari_count and tamil_count > latin_count):
            confidence = min(0.99, 0.70 + (tamil_ratio * 0.30))
            return {
                "language": "ta",
                "language_name": "Tamil",
                "confidence": round(confidence, 3),
                "script": "Tamil",
                "details": {"tamil_ratio": round(tamil_ratio, 3), "char_count": tamil_count}
            }

        # 2. Devanagari Script check (Hindi vs Marathi disambiguation)
        if devanagari_ratio >= 0.35 or (devanagari_count >= 5 and devanagari_count > latin_count):
            # Check for Marathi-specific character ळ (\u0933)
            marathi_char_matches = len(MARATHI_SPECIFIC_CHARS.findall(clean_text))
            
            # Tokenize words for vocabulary matching
            words = [w.strip() for w in re.split(r'[\s\.,!?;:\"\'\(\)\[\]।॥]+', clean_text) if w.strip()]
            
            mr_matches = sum(1 for w in words if w in MARATHI_STOPWORDS)
            hi_matches = sum(1 for w in words if w in HINDI_STOPWORDS)

            # Marathi indicators
            if marathi_char_matches > 0 or mr_matches > hi_matches:
                confidence = 0.95 if marathi_char_matches > 0 else min(0.92, 0.70 + (mr_matches / max(1, len(words))) * 0.5)
                return {
                    "language": "mr",
                    "language_name": "Marathi",
                    "confidence": round(confidence, 3),
                    "script": "Devanagari",
                    "details": {
                        "devanagari_ratio": round(devanagari_ratio, 3),
                        "marathi_chars": marathi_char_matches,
                        "mr_vocab_matches": mr_matches,
                        "hi_vocab_matches": hi_matches
                    }
                }
            else:
                # Default Devanagari to Hindi if no strong Marathi signals
                confidence = min(0.96, 0.75 + (hi_matches / max(1, len(words))) * 0.4 if hi_matches > 0 else 0.80)
                return {
                    "language": "hi",
                    "language_name": "Hindi",
                    "confidence": round(confidence, 3),
                    "script": "Devanagari",
                    "details": {
                        "devanagari_ratio": round(devanagari_ratio, 3),
                        "marathi_chars": marathi_char_matches,
                        "mr_vocab_matches": mr_matches,
                        "hi_vocab_matches": hi_matches
                    }
                }

        # 3. Latin Script (English)
        if latin_ratio >= 0.40:
            confidence = min(0.99, 0.70 + (latin_ratio * 0.30))
            return {
                "language": "en",
                "language_name": "English",
                "confidence": round(confidence, 3),
                "script": "Latin",
                "details": {"latin_ratio": round(latin_ratio, 3), "char_count": latin_count}
            }

        return {
            "language": "und",
            "language_name": "Undetermined",
            "confidence": 0.30,
            "script": "Mixed",
            "details": {
                "tamil_ratio": round(tamil_ratio, 3),
                "devanagari_ratio": round(devanagari_ratio, 3),
                "latin_ratio": round(latin_ratio, 3)
            }
        }

    @classmethod
    def is_supported_language(cls, lang_code: Optional[str]) -> bool:
        if not lang_code:
            return False
        return lang_code.lower().strip() in SUPPORTED_LANGUAGES

    @classmethod
    def validate_language_match(cls, expected_lang: str, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates whether the detected language matches the expected source language.
        Returns: (is_match: bool, detected_lang: str, detection_result: Dict)
        """
        result = cls.detect_language(text)
        det_lang = result["language"]
        exp = expected_lang.lower().strip()

        # If expected is broad "multilingual", accept any supported language
        if exp in ["all", "multi", "multilingual"]:
            return det_lang in SUPPORTED_LANGUAGES, det_lang, result

        # Exact match or high confidence alignment
        if det_lang == exp:
            return True, det_lang, result

        # If text is too short or ambiguous but contains proper script
        if exp == "ta" and result["script"] == "Tamil":
            return True, "ta", result
        if exp in ["hi", "mr"] and result["script"] == "Devanagari":
            # Allow fallback if detection was low confidence between Hindi and Marathi
            if result["confidence"] < 0.65:
                return True, exp, result

        return False, det_lang, result
