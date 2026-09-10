import re
import unicodedata
from typing import List, Dict, Any, Optional
from app.utils.language_detector import LanguageDetector

class ClaimExtractor:
    """
    Extracts standalone factual claim candidates from articles, press releases,
    and fact-check reports across English, Tamil, Hindi, and Marathi.
    """

    # Unresolved pronouns or connecting phrases at the start of a sentence
    DANGLING_STARTS = [
        # English
        "he ", "she ", "they ", "it ", "this ", "these ", "those ", "which ",
        "however,", "therefore,", "moreover,", "furthermore,", "meanwhile,",
        "additionally,", "also,", "accordingly,", "consequently,", "in addition,",
        # Tamil
        "அவர் ", "அவர்கள் ", "இது ", "இவை ", "எனவே ", "மேலும் ", "இதற்கிடையில் ",
        # Hindi
        "वह ", "वे ", "यह ", "ये ", "उन्होंने ", "हालांकि ", "इसलिए ", "इसके अलावा ",
        # Marathi
        "तो ", "ती ", "ते ", "यांनी ", "त्यांनी ", "हे ", "मात्र ", "त्यामुळे ", "शिवाय "
    ]

    # Subjective / opinion indicator words
    OPINION_MARKERS = [
        # English
        "i think", "i believe", "in my opinion", "seems to me", "should ideally",
        "might possibly", "perhaps one can", "arguably", "feels like", "in my view",
        # Tamil
        "என் கருத்துப்படி", "நான் நினைக்கிறேன்", "தோன்றுகிறது", "வாய்ப்புள்ளது",
        # Hindi
        "मेरी राय में", "मुझे लगता है", "संभवतः", "शायद",
        # Marathi
        "माझ्या मते", "मला वाटते", "कदाचित", "असावे"
    ]

    # Factual signal verbs and phrases common in verifiable claims
    FACT_SIGNALS = [
        # English
        "announced", "stated", "passed", "quashed", "acquitted", "sentenced",
        "approved", "launched", "directed", "ruled", "held", "decided",
        "introduced", "mandated", "reported", "confirmed", "rejected", "banned",
        "allocated", "signed", "notified", "constituted", "filed", "dismissed",
        # Tamil
        "அறிவித்தது", "தெரிவித்தது", "உத்தரவிட்டது", "ரத்து செய்தது", "விடுதலை செய்தது",
        "தண்டனை விதித்தது", "ஒப்புதல் அளித்தது", "தொடங்கியது", "தீர்ப்பளித்தது", "உறுதிப்படுத்தியது",
        "நிராகரித்தது", "தடை விதித்தது", "கையொப்பமிட்டது", "தாக்கல் செய்தது", "வெளியிட்டது",
        # Hindi
        "घोषणा की", "कहा", "बताया", "रद्द किया", "बरी किया", "सजा सुनाई",
        "मंजूरी दी", "शुरू किया", "आदेश दिया", "फैसला सुनाया", "पुष्टि की",
        "खारिज किया", "प्रतिबंध लगाया", "हस्ताक्षर किए", "दायर किया", "जारी किया",
        # Marathi
        "जाहीर केले", "सांगितले", "रद्द केले", "निर्दोष मुक्त केले", "शिक्षा सुनावली",
        "मंजुरी दिली", "सुरू केले", "आदेश दिले", "निकाल दिला", "पुष्टी केली",
        "फेटाळले", "बंदी घातली", "स्वाक्षरी केली", "दाखल केले", "प्रसिद्ध केले"
    ]

    @staticmethod
    def extract_claims_from_text(
        text: str,
        title: Optional[str] = None,
        source_type: Optional[str] = None,
        min_words: int = 5,
        max_words: int = 60
    ) -> List[Dict[str, Any]]:
        candidates = []

        # If title is substantive and standalone, consider title as a prime claim candidate
        if title and ClaimExtractor.is_valid_standalone_claim(title):
            norm_title = ClaimExtractor.normalize_claim(title)
            lang_info = LanguageDetector.detect_language(norm_title)
            candidates.append({
                "claim_text": norm_title,
                "source_type": source_type or "news",
                "origin": "title",
                "language": lang_info["language"],
                "confidence": 0.88
            })

        # Break text into candidate sentences
        sentences = ClaimExtractor._split_sentences(text)
        for sent in sentences:
            sent_clean = ClaimExtractor.normalize_claim(sent)
            words = sent_clean.split()
            if len(words) < min_words or len(words) > max_words:
                continue

            if ClaimExtractor.is_valid_standalone_claim(sent_clean):
                score = ClaimExtractor._score_claim_quality(sent_clean)
                if score >= 0.45:
                    lang_info = LanguageDetector.detect_language(sent_clean)
                    candidates.append({
                        "claim_text": sent_clean,
                        "source_type": source_type or "article_body",
                        "origin": "body",
                        "language": lang_info["language"],
                        "confidence": round(score, 3)
                    })

        # Deduplicate candidates within the document
        unique_candidates = []
        seen = set()
        for cand in candidates:
            norm = re.sub(r'[\s\.,!?;:\"\'\(\)\[\]।॥]+', ' ', cand["claim_text"].lower()).strip()
            if norm not in seen:
                seen.add(norm)
                unique_candidates.append(cand)

        return unique_candidates

    @staticmethod
    def is_valid_standalone_claim(sentence: str) -> bool:
        sent = unicodedata.normalize("NFC", sentence.strip())
        if len(sent) < 20:
            return False
        
        sent_lower = sent.lower()

        # Check for rhetorical or interrogative statements
        if sent.endswith("?"):
            return False

        # Filter dangling pronouns at sentence start
        for dangler in ClaimExtractor.DANGLING_STARTS:
            if sent_lower.startswith(dangler):
                return False

        # Filter heavy opinion markers
        for op in ClaimExtractor.OPINION_MARKERS:
            if op in sent_lower:
                return False

        lang_info = LanguageDetector.detect_language(sent)
        detected_lang = lang_info["language"]

        # Number / Year detection (supports Latin and Indic numerals)
        has_number_or_year = bool(re.search(
            r'(\b\d{1,6}\b|crore|lakh|percent|%|million|billion|கோடி|லட்சம்|சதவீதம்|करोड़|लाख|प्रतिशत|टक्के)',
            sent_lower
        ))

        # Check for presence of factual action verbs
        has_fact_verb = any(v in sent_lower for v in ClaimExtractor.FACT_SIGNALS)

        # Language-specific criteria
        if detected_lang in ["ta", "hi", "mr"]:
            # For Indian languages, sentence must have substantial length and either a factual signal, number, or standard length
            has_indic_chars = len(sent) >= 25
            return has_fact_verb or has_number_or_year or has_indic_chars
        else:
            # For English: named entities, numbers, or action verbs
            has_named_entity = bool(re.search(r"\b[A-Z][a-z]{2,}\b", sent))
            has_standard_verb = bool(re.search(r"\b(is|was|are|were|has|have|had|will|would|can|could|did|does)\b", sent_lower))
            return has_fact_verb or (has_standard_verb and has_named_entity) or (has_named_entity and has_number_or_year)

    @staticmethod
    def _score_claim_quality(claim: str) -> float:
        score = 0.5
        claim_lower = claim.lower()
        
        # Reward specific named entities across languages
        indic_entities = [
            # English
            "india", "government", "court", "high court", "supreme court", "pib", "isro",
            "parliament", "ministry", "minister", "rbi", "delhi", "karnataka", "maharashtra",
            "cabinet", "commission", "police", "scheme", "act", "bill", "order",
            # Tamil
            "இந்தியா", "அரசு", "நீதிமன்றம்", "உயர் நீதிமன்றம்", "உச்ச நீதிமன்றம்", "அமைச்சகம்",
            "அமைச்சர்", "காவல்துறை", "திட்டம்", "சட்டம்", "ஆணை", "தமிழ்நாடு",
            # Hindi
            "भारत", "सरकार", "कोर्ट", "हाई कोर्ट", "सुप्रीम कोर्ट", "मंत्रालय",
            "मंत्री", "पुलिस", "योजना", "विधेयक", "आदेश", "संसद",
            # Marathi
            "भारत", "शासन", "न्यायालय", "उच्च न्यायालय", "सर्वोच्च न्यायालय", "मंत्रालय",
            "मंत्री", "पोलीस", "योजना", "कायदा", "आदेश", "महाराष्ट्र"
        ]
        if any(e in claim_lower for e in indic_entities):
            score += 0.2

        # Reward presence of concrete dates or numbers
        if re.search(r'(\b\d{1,4}\b|\b20\d\d\b|கோடி|करोड़|लाख|टक्के|%)', claim_lower):
            score += 0.15

        # Reward strong verifiable factual verbs
        if any(v in claim_lower for v in ClaimExtractor.FACT_SIGNALS):
            score += 0.15

        return min(1.0, score)

    @staticmethod
    def normalize_claim(text: str) -> str:
        text = unicodedata.normalize("NFC", text.strip())
        # Remove quotes surrounding whole claim
        text = re.sub(r'^["\'“‘]+|["\'”’]+$', '', text.strip())
        # Remove reading time and timestamp prefixes
        text = re.sub(r'^\d+\s*min\s+read[A-Za-z\s\d,:]+(IST|GMT|UTC|PM|AM)\s*', '', text, flags=re.IGNORECASE)
        # Remove prefix tags in English, Tamil, Hindi, Marathi
        text = re.sub(
            r'^(fact\s*check|explained|exclusive|watch|report|analysis|live|breaking|உண்மை\s*சரிபார்ப்பு|फैक्ट\s*चेक|फॅक्ट\s*चेक)\s*:\s*',
            '', text, flags=re.IGNORECASE
        )
        # Remove common trailing publisher suffixes
        text = re.sub(r'\s*\|\s*(Legal News|News|India News|Explained|Opinion)?\s*[-–—]\s*.*$', '', text, flags=re.IGNORECASE)
        # Normalize spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """Split on sentence boundaries for English and Indic scripts (., !, ?, ।, ॥)."""
        clean_text = unicodedata.normalize("NFC", text)
        clean_text = re.sub(r'(Mr|Mrs|Dr|Govt|Prof|Sr|Jr|Vs|vs|pvt|ltd|approx|e\.g|i\.e)\.', r'\1<DOT>', clean_text, flags=re.IGNORECASE)
        parts = re.split(r'(?<=[.!?।॥])\s+', clean_text)
        restored = [p.replace("<DOT>", ".").strip() for p in parts if p.strip()]
        return restored
