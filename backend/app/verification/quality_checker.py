import unicodedata
from typing import Tuple, Optional, Dict, Any
from app.utils.language_detector import LanguageDetector

class QualityChecker:
    """
    Performs comprehensive automated validation on claim-evidence pairs before
    ingestion into the final training dataset for English, Tamil, Hindi, and Marathi.
    """

    def __init__(
        self,
        min_claim_length: int = 15,
        max_claim_length: int = 450,
        min_evidence_length: int = 40,
        max_evidence_length: int = 1800,
        min_relevance_score: float = 0.22,
        min_confidence_score: float = 0.60
    ):
        self.min_claim_length = min_claim_length
        self.max_claim_length = max_claim_length
        self.min_evidence_length = min_evidence_length
        self.max_evidence_length = max_evidence_length
        self.min_relevance_score = min_relevance_score
        self.min_confidence_score = min_confidence_score

    def validate(
        self,
        claim: str,
        evidence: str,
        label: Optional[str],
        match_score: float,
        confidence: float,
        is_duplicate: bool = False,
        duplicate_reason: str = "",
        expected_language: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        claim_clean = unicodedata.normalize("NFC", claim.strip())
        evidence_clean = unicodedata.normalize("NFC", evidence.strip())

        # 1. Duplicate check
        if is_duplicate:
            return False, f"Duplicate detected: {duplicate_reason}", {"check": "duplicate"}

        if claim_clean.lower() == evidence_clean.lower():
            return False, "Claim and evidence cannot be identical text", {"check": "identical"}

        # 2. Claim length check
        if len(claim_clean) < self.min_claim_length:
            return False, f"Claim too short ({len(claim_clean)} chars < min {self.min_claim_length})", {"check": "claim_length"}
        if len(claim_clean) > self.max_claim_length:
            return False, f"Claim too long ({len(claim_clean)} chars > max {self.max_claim_length})", {"check": "claim_length"}

        # 3. Evidence length check
        if len(evidence_clean) < self.min_evidence_length:
            return False, f"Evidence too short ({len(evidence_clean)} chars < min {self.min_evidence_length})", {"check": "evidence_length"}
        if len(evidence_clean) > self.max_evidence_length:
            return False, f"Evidence too long ({len(evidence_clean)} chars > max {self.max_evidence_length})", {"check": "evidence_length"}

        # 4. Language check
        lang_res = LanguageDetector.detect_language(claim_clean)
        detected_lang = lang_res["language"]
        if not LanguageDetector.is_supported_language(detected_lang):
            return False, f"Unsupported or undetermined language: '{detected_lang}'", {"check": "language", "detected": detected_lang}

        if expected_language and expected_language not in ["all", "multi", "multilingual"]:
            is_match, _, _ = LanguageDetector.validate_language_match(expected_language, claim_clean)
            if not is_match:
                return False, f"Language mismatch (Expected: {expected_language}, Detected: {detected_lang})", {"check": "language_match", "detected": detected_lang}

        # 5. Relevance match check
        if match_score < self.min_relevance_score:
            return False, f"Low semantic relevance between claim and evidence (score {round(match_score, 2)} < {self.min_relevance_score})", {"check": "relevance"}

        # 6. Label validity check
        if not label or label not in ["SUPPORTS", "REFUTES"]:
            return False, "Unclear verification label (neither clear SUPPORTS nor REFUTES)", {"check": "label"}

        # 7. Confidence threshold check
        if confidence < self.min_confidence_score:
            return False, f"Label confidence below threshold ({round(confidence, 2)} < {self.min_confidence_score})", {"check": "confidence"}

        return True, "Passed quality checks", {
            "check": "passed",
            "language": detected_lang,
            "confidence": confidence,
            "match_score": match_score
        }
