import re
import math
import unicodedata
from typing import Dict, Any, List, Set
from collections import Counter
from app.crawlers.topic_filter import TopicRelevanceFilter

class CandidateMatcher:
    """
    Ranks and scores candidate evidence for a given claim across English, Tamil,
    Hindi, and Marathi based on:
    - Named entity & key term alignment
    - Unicode TF-IDF / N-gram cosine similarity
    - Token Jaccard similarity
    - Numeric and date alignment
    """

    @classmethod
    def compute_match_score(cls, claim: str, evidence: str) -> Dict[str, Any]:
        claim_clean = unicodedata.normalize("NFC", claim.strip())
        evidence_clean = unicodedata.normalize("NFC", evidence.strip())

        claim_tokens = cls._tokenize(claim_clean)
        evidence_tokens = cls._tokenize(evidence_clean)

        claim_entities = cls._extract_entity_words(claim_clean)
        evidence_entities = cls._extract_entity_words(evidence_clean)

        # 1. Entity overlap
        entity_overlap = 0.0
        if claim_entities:
            matched_entities = set()
            for ce in claim_entities:
                for ee in evidence_entities:
                    if ce == ee or ce in ee or ee in ce:
                        matched_entities.add(ce)
                        break
            entity_overlap = len(matched_entities) / len(claim_entities)
        else:
            # If no discrete entities found, default to token overlap
            entity_overlap = 0.5

        # 2. Token Jaccard similarity
        claim_token_set = set(claim_tokens)
        evidence_token_set = set(evidence_tokens)
        jaccard = len(claim_token_set.intersection(evidence_token_set)) / max(1, len(claim_token_set.union(evidence_token_set)))

        # 3. Cosine similarity on tokens
        cosine_sim = cls._cosine_similarity(claim_tokens, evidence_tokens)

        # 4. Numerical / Year alignment
        claim_nums = set(re.findall(r'(\b\d{1,6}\b|கோடி|करोड़|लाख|टक्के)', claim_clean.lower()))
        evidence_nums = set(re.findall(r'(\b\d{1,6}\b|கோடி|करोड़|लाख|टक्के)', evidence_clean.lower()))
        num_overlap = 1.0
        if claim_nums:
            matched_nums = claim_nums.intersection(evidence_nums)
            num_overlap = len(matched_nums) / len(claim_nums)

        # Composite score
        composite_score = (
            (entity_overlap * 0.40) +
            (cosine_sim * 0.35) +
            (jaccard * 0.15) +
            (num_overlap * 0.10)
        )

        return {
            "score": round(composite_score, 4),
            "entity_overlap": round(entity_overlap, 3),
            "cosine_sim": round(cosine_sim, 3),
            "jaccard": round(jaccard, 3),
            "is_relevant": composite_score >= 0.22,
            "matched_entities": list(claim_entities.intersection(evidence_entities)) if claim_entities else []
        }

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        """Unicode token extraction across English and Indian scripts."""
        words = re.findall(r'[\w\'-]+', text.lower(), flags=re.UNICODE)
        return [w for w in words if w not in TopicRelevanceFilter.STOP_WORDS and len(w) >= 2]

    @classmethod
    def _extract_entity_words(cls, text: str) -> Set[str]:
        entities = set()
        # English capitalized words
        for w in re.findall(r'\b[A-Za-z0-9_\'-]+\b', text):
            if len(w) >= 3 and (w[0].isupper() or w.isupper()):
                w_clean = w.lower()
                if w_clean not in TopicRelevanceFilter.STOP_WORDS:
                    entities.add(w_clean)

        # Prominent multilingual entities and phrases
        lower_text = text.lower()
        domain_phrases = [
            # English
            "high court", "supreme court", "life sentence", "murder case",
            "fact check", "covid-19", "press information bureau", "union cabinet",
            # Tamil
            "உயர் நீதிமன்றம்", "உச்ச நீதிமன்றம்", "நீதிமன்றம்", "தகவல் பணியகம்",
            "மத்திய அரசு", "தமிழ்நாடு", "காவல்துறை",
            # Hindi
            "हाई कोर्ट", "सुप्रीम कोर्ट", "पत्र सूचना कार्यालय", "केंद्र सरकार",
            "मंत्रालय", "पुलिस", "योजना",
            # Marathi
            "उच्च न्यायालय", "सर्वोच्च न्यायालय", "मंत्रालय", "शासन", "महाराष्ट्र शासन"
        ]
        for dp in domain_phrases:
            if dp in lower_text:
                entities.add(dp)

        # For Indian scripts, also treat substantial nouns (>3 chars) as entity candidates
        indic_tokens = re.findall(r'[\u0B80-\u0BFF\u0900-\u097F]{4,}', text)
        for it in indic_tokens:
            if it not in TopicRelevanceFilter.STOP_WORDS:
                entities.add(it)

        return entities

    @classmethod
    def _cosine_similarity(cls, tokens1: List[str], tokens2: List[str]) -> float:
        if not tokens1 or not tokens2:
            return 0.0
        vec1 = Counter(tokens1)
        vec2 = Counter(tokens2)

        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        sum1 = sum([vec1[x]**2 for x in vec1.keys()])
        sum2 = sum([vec2[x]**2 for x in vec2.keys()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator
