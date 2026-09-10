import re
import unicodedata
from typing import Dict, Any, Optional, Tuple

class LabelGenerator:
    """
    Determines the verification relationship between a CLAIM and EVIDENCE across
    English, Tamil, Hindi, and Marathi:
    - SUPPORTS: Evidence clearly affirms/confirms the factual claim (Mapped to 1).
    - REFUTES: Evidence directly contradicts, debunks, or refutes the claim (Mapped to 0).
    - None / Low-Confidence: Evidence is ambiguous, merely topical, or insufficient.
    """

    # Fact-checking debunking phrases (High-confidence REFUTES indicators)
    FACTCHECK_DEBUNK_PHRASES = [
        # English
        "fake news", "false claim", "debunked", "misleading", "fact check finds",
        "no such announcement", "baseless", "untrue", "doctored video", "fabricated",
        "clarified that it is fake", "did not say", "never happened", "hoax",
        "contrary to the viral claim", "official clarified that", "falsely claimed",
        "morphed image", "refuted claims", "no truth in", "categorically denied",
        # Tamil
        "போலி செய்தி", "தவறான தகவல்", "உண்மையல்ல", "வதந்தி", "உண்மை என்ன",
        "மறுப்பு", "போலியான", "எந்த அறிவிப்பும் வெளியிடவில்லை", "தவறான கூற்று",
        "மறுத்துள்ளது", "உண்மையில்லை", "திரிக்கப்பட்ட",
        # Hindi
        "फर्जी खबर", "झूठा दावा", "भ्रामक", "गलत दावा", "सच्चाई क्या है",
        "फेक न्यूज", "खारिज किया", "कोई घोषणा नहीं की", "दावा गलत है",
        "अफवाह", "दावा फर्जी", "तथ्यहीन", "वायरल दावा गलत",
        # Marathi
        "खोटा दावा", "अफवा", "दिशाभूल करणारा", "सत्य काय", "फेक न्यूज",
        "दावा खोटा", "कोणतीही घोषणा नाही", "दावा खोटा आहे", "दावा चुकीचा",
        "अफवा पसरवली", "असा कोणताही निर्णय नाही"
    ]

    # Contradiction / Negation / Antonym tokens and patterns
    NEGATION_WORDS = {
        # English
        "not", "no", "never", "neither", "nor", "none", "nobody", "nowhere",
        "denied", "refuted", "rejected", "quashed", "acquitted", "dismissed",
        "set aside", "overturned", "cancelled", "prohibited", "banned", "false",
        # Tamil
        "இல்லை", "அல்ல", "மறுத்தது", "ரத்து", "கிடையாது", "தவறு", "நிராகரித்தது",
        "தடை", "விடுதலை",
        # Hindi
        "नहीं", "न", "कभी नहीं", "खारिज", "रद्द", "गलत", "झूठा", "मना",
        "प्रतिबंधित", "बरी", "अस्वीकार",
        # Marathi
        "नाही", "नसून", "रद्द", "खोटे", "नकार", "फेटाळले", "बंदी", "निर्दोष"
    }

    # Affirmative / Confirmation tokens
    CONFIRMATION_PHRASES = [
        # English
        "confirmed", "announced", "officially launched", "upheld", "affirmed",
        "approved", "notified", "passed the order", "found guilty", "sentenced",
        "ruled that", "directed the", "stated that", "inaugurated", "signed an agreement",
        # Tamil
        "உறுதிப்படுத்தியது", "அறிவித்தது", "தீர்ப்பு", "ஒப்புதல்", "வெளியிட்டது",
        "உத்தரவிட்டது", "தொடங்கிவைத்தார்", "ஒப்பந்தம் கையெழுத்தானது", "அறிவிப்பு",
        # Hindi
        "पुष्टि की", "घोषणा की", "मंजूरी दी", "फैसला सुनाया", "आदेश दिया",
        "जारी किया", "उद्घाटन किया", "सहमति बनी", "लागू किया", "घोषणा",
        # Marathi
        "पुष्टी केली", "जाहीर केले", "घोषणा केली", "मंजुरी दिली", "निकाल दिला", "आदेश दिले",
        "सुरू केले", "उद्घाटन केले", "स्वाक्षरी केली", "लागू केले", "घोषणा"
    ]

    # Antonym pairs for direct contradiction detection
    ANTONYM_PAIRS = [
        # English
        ("mandatory", "voluntary"),
        ("compulsory", "optional"),
        ("allowed", "banned"),
        ("permitted", "prohibited"),
        ("increased", "decreased"),
        ("hiked", "slashed"),
        ("approved", "rejected"),
        ("guilty", "acquitted"),
        ("convicted", "acquitted"),
        ("upheld", "quashed"),
        ("upheld", "set aside"),
        ("won", "lost"),
        ("alive", "dead"),
        ("success", "failure"),
        ("launched", "deferred"),
        ("started", "cancelled"),
        # Hindi / Marathi / Tamil polar antonym pairs
        ("अनिवार्य", "स्वैच्छिक"),
        ("सत्य", "असत्य"),
        ("मंजूर", "रद्द"),
        ("கட்டாயம்", "விருப்பத்தின்படி")
    ]

    @classmethod
    def generate_label(
        cls,
        claim: str,
        evidence: str,
        match_score: float = 0.5,
        source_type: Optional[str] = None
    ) -> Tuple[Optional[str], float, str]:
        """
        Returns: (Label ["SUPPORTS" | "REFUTES" | None], confidence [0.0 - 1.0], reason)
        """
        claim_clean = unicodedata.normalize("NFC", claim.strip())
        evidence_clean = unicodedata.normalize("NFC", evidence.strip())

        claim_lower = claim_clean.lower()
        evidence_lower = evidence_clean.lower()

        # 1. Check Fact-Check debunking indicators (Primary source of REFUTES)
        for phrase in cls.FACTCHECK_DEBUNK_PHRASES:
            if phrase in evidence_lower:
                confidence = 0.94
                return "REFUTES", confidence, f"Evidence contains explicit debunking marker: '{phrase}'"

        # 2. Check Antonym Contradictions
        for word_a, word_b in cls.ANTONYM_PAIRS:
            if (word_a in claim_lower and word_b in evidence_lower) or (word_b in claim_lower and word_a in evidence_lower):
                confidence = 0.88
                return "REFUTES", confidence, f"Semantic polarity conflict detected: '{word_a}' vs '{word_b}'"

        # 3. Check Explicit Negation Flip
        claim_has_neg = any(w in claim_lower for w in cls.NEGATION_WORDS)
        evidence_has_neg = any(w in evidence_lower for w in cls.NEGATION_WORDS)

        # Check Legal acquittals / set-aside verdicts
        legal_acquittal_markers = ["set aside", "acquitted", "quashed", "ரத்து செய்தது", "விடுதலை செய்தது", "बरी किया", "निर्दोष मुक्त"]
        if any(m in evidence_lower for m in legal_acquittal_markers):
            if any(m in claim_lower for m in legal_acquittal_markers):
                return "SUPPORTS", 0.90, "Both claim and evidence corroborate acquittal / quashed verdict"
            elif any(c in claim_lower for c in ["convicted", "sentenced", "தண்டனை", "दोषी", "शिक्षा"]):
                return "REFUTES", 0.88, "Court verdict (acquittal) refutes conviction claim"

        # If negation conflict exists on relevant topic
        if claim_has_neg != evidence_has_neg and match_score < 0.85 and claim_clean not in evidence_clean:
            if match_score >= 0.28:
                return "REFUTES", round(min(0.92, 0.70 + match_score * 0.25), 2), "Negation discrepancy on shared entity/topic"

        # 4. Check Direct Affirmation / Support
        for phrase in cls.CONFIRMATION_PHRASES:
            if phrase in evidence_lower and match_score >= 0.28:
                confidence = round(min(0.95, 0.75 + match_score * 0.20), 2)
                return "SUPPORTS", confidence, f"Evidence affirms factual event with marker: '{phrase}'"

        # 5. Check High-confidence factual paraphrase / alignment
        if match_score >= 0.75 and claim_has_neg == evidence_has_neg:
            confidence = round(min(0.92, 0.70 + match_score * 0.20), 2)
            return "SUPPORTS", confidence, "High-confidence factual alignment"

        # 6. Moderate match with government / official source
        if source_type == "government" and match_score >= 0.35 and claim_has_neg == evidence_has_neg:
            return "SUPPORTS", round(min(0.90, 0.65 + match_score * 0.25), 2), "Official source affirms factual statement"

        # 7. Uncertain / Ambiguous / Topical Only (DO NOT FABRICATE LABELS)
        return None, 0.40, "Ambiguous claim-evidence relationship; requires explicit confirmation or debunking marker"
