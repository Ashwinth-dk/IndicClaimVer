import re
import unicodedata
from typing import List, Dict, Any, Optional
from app.crawlers.topic_filter import TopicRelevanceFilter

class EvidenceExtractor:
    """
    Extracts high-quality, context-preserving evidence passages from independent articles
    that address a target claim across English, Tamil, Hindi, and Marathi.
    """

    @staticmethod
    def extract_evidence_candidates(
        article_paragraphs: List[str],
        claim_text: str,
        min_length: int = 40,
        max_length: int = 900
    ) -> List[Dict[str, Any]]:
        claim_keywords = EvidenceExtractor._get_keywords(claim_text)
        candidates = []

        for i, para in enumerate(article_paragraphs):
            para_clean = unicodedata.normalize("NFC", para.strip())
            if len(para_clean) < min_length:
                continue

            # If paragraph is very long, optionally trim to relevant sentences
            if len(para_clean) > max_length:
                para_clean = EvidenceExtractor._extract_relevant_sentences(para_clean, claim_keywords, max_length)

            para_lower = para_clean.lower()
            keyword_matches = [kw for kw in claim_keywords if kw in para_lower]
            overlap_ratio = len(keyword_matches) / max(1, len(claim_keywords))

            # If there's meaningful keyword/entity overlap, consider as candidate
            if overlap_ratio >= 0.20 or len(keyword_matches) >= 2 or (len(claim_keywords) <= 2 and len(keyword_matches) >= 1):
                candidates.append({
                    "evidence_text": para_clean,
                    "overlap_ratio": round(overlap_ratio, 3),
                    "matched_keywords": keyword_matches,
                    "paragraph_index": i
                })

        # Sort by overlap ratio descending
        candidates.sort(key=lambda x: x["overlap_ratio"], reverse=True)
        return candidates

    @staticmethod
    def _extract_relevant_sentences(text: str, keywords: List[str], max_length: int) -> str:
        sentences = re.split(r'(?<=[.!?।॥])\s+', text)
        scored_sentences = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            s_lower = s_clean.lower()
            matches = sum(1 for kw in keywords if kw in s_lower)
            scored_sentences.append((matches, s_clean))

        if not scored_sentences:
            return text[:max_length]

        selected = []
        curr_len = 0
        for matches, s in scored_sentences:
            if matches > 0 or len(selected) == 0:
                if curr_len + len(s) + 1 <= max_length:
                    selected.append(s)
                    curr_len += len(s) + 1

        return " ".join(selected) if selected else text[:max_length]

    @staticmethod
    def _get_keywords(text: str) -> List[str]:
        """Extract substantive Unicode tokens across English, Tamil, Hindi, and Marathi."""
        norm_text = unicodedata.normalize("NFC", text).lower()
        tokens = re.findall(r'[\w\'-]+', norm_text, flags=re.UNICODE)
        return [t for t in tokens if t not in TopicRelevanceFilter.STOP_WORDS and len(t) >= 2]
