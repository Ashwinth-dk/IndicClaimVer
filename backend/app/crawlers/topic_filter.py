"""
Topic & Two-Stage Query Relevance Evaluator for IndicClaim.
Performs Pre-Fetch Snippet Filtering (Stage 1) and Post-Fetch Deep Content
& Temporal Relevance Validation (Stage 2) across English, Tamil, Hindi, and Marathi.
"""

import re
import unicodedata
from datetime import datetime
from typing import Set, List, Tuple, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.crawlers.query_intent import QueryIntent, QueryIntentAnalyzer
from app.utils.language_detector import LanguageDetector


class QueryRelevanceDiagnostics(BaseModel):
    """Detailed audit record of why a document was accepted or rejected."""
    query_id: str
    canonical_query: str
    target_language: str
    relevance_score: float
    is_accepted: bool
    stage: str  # "STAGE_1_PREFETCH" or "STAGE_2_CONTENT"
    
    # Detailed factor matches
    topic_match: bool = False
    event_match: bool = False
    date_match: bool = False
    cooccurrence_match: bool = False
    
    # Temporal breakdown
    extracted_year: Optional[int] = None
    extracted_pub_date: Optional[str] = None
    is_temporal_valid: bool = True
    
    # Audit log
    reasons: List[str] = Field(default_factory=list)
    rejection_reason: Optional[str] = None
    source_quality_score: float = 1.0


class TopicRelevanceFilter:
    """
    Two-Stage Query-Driven Relevance Evaluator.
    Filters out off-topic, stale, or spurious articles across EN, TA, HI, and MR.
    """

    STOP_WORDS: Set[str] = {
        # English stop words
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
        "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
        "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
        "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
        "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
        "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
        "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
        "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
        "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
        "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
        "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
        "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
        "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
        "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
        "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
        "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
        "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
        "yourself", "yourselves",
        # Generic noise tokens
        "news", "latest", "today", "update", "updates", "report", "reports", "official",
        "information", "details", "article", "articles", "breaking", "exclusive", "read",
        "view", "watch", "download", "online", "free",
        # Tamil stop words
        "மற்றும்", "ஒரு", "இந்த", "அந்த", "என்று", "ஆனால்", "அல்லது", "என",
        "செய்திகள்", "சமீபத்திய", "இன்று", "தகவல்", "விவரங்கள்", "அறிக்கை",
        "அவர்", "அவர்கள்", "இது", "அது", "உள்ளது", "உள்ளன", "இருந்தது", "இருக்கின்றது",
        # Hindi stop words
        "है", "हैं", "था", "थी", "थे", "किया", "की", "के", "का", "को", "में", "पर",
        "नहीं", "और", "या", "लेकिन", "किंतु", "कहा", "बताया", "समाचार", "ताजा", "आज",
        "यह", "वह", "इस", "उस", "ने", "से", "द्वारा", "लिये", "लिए",
        # Marathi stop words
        "आहे", "आहेत", "होते", "होती", "झाला", "झाली", "झाले", "केले", "केली", "केला",
        "नाही", "यांनी", "म्हणून", "आणि", "पण", "परंतु", "किंवा", "बातम्या", "ताजी", "आज",
        "हे", "ते", "या", "त्या", "मध्ये", "वरील"
    }

    UNWANTED_PATTERNS = [
        r"\bcasino\b", r"\blottery\b", r"\bporn\b", r"\bxxx\b", r"\bstream\s+online\b",
        r"\bdownload\s+mp3\b", r"\bfree\s+movie\b", r"\brecipes\b", r"\binstagram\s+viewer\b",
        r"\bhoroscope\b", r"\bastrology\b", r"\btorrent\b",
        r"ஜோதிடம்", r"ராசிபலன்", r"லாட்டரி", r"राशिफल", r"लॉटरी", r"सट्टा"
    ]

    # Authoritative and verified domains
    AUTHORITATIVE_DOMAINS = [
        "pib.gov.in", "gov.in", "nic.in", "eci.gov.in", "isro.gov.in", "supremecourtofindia.nic.in",
        "factly.in", "boomlive.in", "altnews.in", "thehindu.com", "indianexpress.com",
        "dinamalar.com", "amarujala.com", "loksatta.com", "bbc.com", "livelaw.in"
    ]

    @classmethod
    def normalize_text(cls, text: str) -> str:
        if not text:
            return ""
        return unicodedata.normalize("NFC", str(text)).strip()

    @classmethod
    def extract_keywords(cls, query: str) -> List[str]:
        norm_q = cls.normalize_text(query).lower()
        tokens = re.findall(r'[\w\'-]+', norm_q, flags=re.UNICODE)
        keywords = [t for t in tokens if t not in cls.STOP_WORDS and len(t) >= 2]
        return keywords or [t for t in tokens if len(t) >= 2]

    @classmethod
    def extract_years_and_dates(cls, text: str) -> List[int]:
        """Extracts 4-digit years (e.g. 2024, 2025, 2026)."""
        matches = re.findall(r"\b(20[1-3][0-9])\b", text)
        return [int(m) for m in matches]

    @classmethod
    def is_relevant(
        cls,
        query: str,
        title: str,
        snippet: str = "",
        min_keyword_overlap: float = 0.20,
        strict_feed_mode: bool = False
    ) -> Tuple[bool, float, List[str]]:
        """
        Lightweight keyword relevance check for individual provider pre-filtering.
        Returns: (is_relevant, score, matched_keywords)
        """
        norm_title = cls.normalize_text(title).lower()
        norm_snippet = cls.normalize_text(snippet).lower()
        combined = f"{norm_title} {norm_snippet}"
        
        # Check spam
        for pat in cls.UNWANTED_PATTERNS:
            if re.search(pat, combined, flags=re.IGNORECASE):
                return False, 0.0, []
                
        keywords = cls.extract_keywords(query)
        if not keywords:
            return True, 1.0, []
            
        matched = [kw for kw in keywords if kw.lower() in combined]
        score = len(matched) / len(keywords) if keywords else 1.0
        
        # Permissive threshold: at least 1 keyword match or fraction >= threshold
        is_rel = (score >= min_keyword_overlap) or (len(matched) >= 1)
        return is_rel, round(score, 2), matched

    # -------------------------------------------------------------------------
    # STAGE 1: PRE-FETCH SNIPPET RELEVANCE FILTER
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_stage1_snippet(
        cls,
        intent: QueryIntent,
        title: str,
        snippet: str = "",
        url: str = "",
        pub_date: str = "",
        source_name: str = "",
        lang: str = "en",
        min_threshold: float = 0.40
    ) -> Tuple[bool, QueryRelevanceDiagnostics]:
        """
        Stage 1 Relevance Filter: Evaluates title, snippet, URL, and metadata
        before downloading the full page.
        """
        title_norm = cls.normalize_text(title).lower()
        snippet_norm = cls.normalize_text(snippet).lower()
        combined_text = f"{title_norm} {snippet_norm} {url.lower()}"
        
        reasons = []
        
        # 1. Spam check
        for pat in cls.UNWANTED_PATTERNS:
            if re.search(pat, combined_text, flags=re.IGNORECASE):
                return False, QueryRelevanceDiagnostics(
                    query_id=intent.query_id,
                    canonical_query=intent.original_query,
                    target_language=lang,
                    relevance_score=0.0,
                    is_accepted=False,
                    stage="STAGE_1_PREFETCH",
                    rejection_reason="Matched spam/unwanted pattern",
                    reasons=["Spam detected in snippet"]
                )

        # 2. Topic Match (Multilingual + Canonical English fallback)
        topic_kws = (
            intent.topic_keywords.get(lang, []) +
            intent.topic_keywords.get("en", []) +
            [intent.topic.lower()]
        )
        topic_match = False
        for kw in topic_kws:
            if kw and (kw in title_norm or kw in snippet_norm or kw in combined_text):
                topic_match = True
                reasons.append(f"Matched topic keyword: '{kw}'")
                break
        
        if not topic_match:
            sub_kws = cls.extract_keywords(intent.topic)
            if any(sk.lower() in combined_text for sk in sub_kws):
                topic_match = True
                reasons.append(f"Matched topic sub-keyword in {lang}")

        # If strict entity mismatch occurs (e.g. "President" when query asks "Vice President")
        if "vice president" in intent.original_query.lower():
            if "president" in combined_text and "vice" not in combined_text and "துணை" not in combined_text and "उप" not in combined_text:
                return False, QueryRelevanceDiagnostics(
                    query_id=intent.query_id,
                    canonical_query=intent.original_query,
                    target_language=lang,
                    relevance_score=0.10,
                    is_accepted=False,
                    stage="STAGE_1_PREFETCH",
                    rejection_reason="Entity mismatch: Mentions President instead of Vice President",
                    reasons=["President found without Vice/उप/துணை modifier"]
                )

        # 3. Event / Action Match
        event_match = False
        if intent.event:
            action_kws = intent.action_keywords.get(lang, [intent.event.lower()]) if intent.action_keywords else [intent.event.lower()]
            for ak in action_kws:
                if ak and (ak in title_norm or ak in snippet_norm or ak in combined_text):
                    event_match = True
                    reasons.append(f"Matched event keyword: '{ak}'")
                    break
        else:
            event_match = True  # No specific action constraint

        # 4. Temporal / Year Match
        date_match = True
        extracted_years = cls.extract_years_and_dates(f"{combined_text} {pub_date}")
        if intent.year:
            if intent.year in extracted_years:
                date_match = True
                reasons.append(f"Matched requested year: {intent.year}")
            elif extracted_years and all(y != intent.year for y in extracted_years):
                # Only explicit non-matching years present (e.g. 2024 when 2026 requested)
                date_match = False
                reasons.append(f"Temporal mismatch: Text mentions {extracted_years} but requested {intent.year}")
            else:
                # Year not explicitly mentioned in short snippet, give provisional benefit of doubt
                date_match = True
                reasons.append("Year not explicitly present in snippet; provisional pass to Stage 2")

        # 5. Source Quality Bonus
        source_quality = 1.0
        if any(auth in url.lower() for auth in cls.AUTHORITATIVE_DOMAINS):
            source_quality = 1.2
            reasons.append("Authoritative / Verified source bonus applied")

        # Compute Stage 1 Relevance Score (Permissive Candidate Discovery)
        topic_score = 0.50 if topic_match else 0.0
        event_score = 0.25 if event_match else 0.10
        date_score = 0.25 if date_match else 0.0
        
        base_score = (topic_score + event_score + date_score)
        final_score = min(1.0, round(base_score * (source_quality if base_score > 0.3 else 1.0), 3))

        # Permissive Rule: Topic matched, temporal compatibility confirmed, score meets threshold
        is_accepted = (final_score >= min_threshold) and topic_match and date_match

        rejection = None
        if not is_accepted:
            if not topic_match:
                rejection = f"Topic '{intent.topic}' not found in search snippet"
            elif not date_match:
                rejection = f"Year '{intent.year}' did not match extracted years {extracted_years}"
            else:
                rejection = f"Relevance score ({final_score:.2f}) below threshold ({min_threshold})"

        diagnostics = QueryRelevanceDiagnostics(
            query_id=intent.query_id,
            canonical_query=intent.original_query,
            target_language=lang,
            relevance_score=final_score,
            is_accepted=is_accepted,
            stage="STAGE_1_PREFETCH",
            topic_match=topic_match,
            event_match=event_match,
            date_match=date_match,
            extracted_year=extracted_years[0] if extracted_years else None,
            extracted_pub_date=pub_date,
            is_temporal_valid=date_match,
            reasons=reasons,
            rejection_reason=rejection,
            source_quality_score=source_quality
        )

        return is_accepted, diagnostics

    # -------------------------------------------------------------------------
    # STAGE 2: FULL ARTICLE CONTENT & TEMPORAL RELEVANCE VALIDATION
    # -------------------------------------------------------------------------
    @classmethod
    def evaluate_stage2_content(
        cls,
        intent: QueryIntent,
        title: str,
        full_text: str,
        pub_date: str = "",
        url: str = "",
        source_name: str = "",
        lang: str = "en",
        min_threshold: float = 0.50
    ) -> Tuple[bool, QueryRelevanceDiagnostics]:
        """
        Stage 2 Relevance Filter: Evaluates complete extracted article content,
        co-occurrence of Topic + Event in text paragraphs, and temporal validation.
        """
        text_norm = cls.normalize_text(full_text)
        title_norm = cls.normalize_text(title).lower()
        full_lower = f"{title_norm} {text_norm.lower()}"
        
        reasons = []

        if len(text_norm) < 80:
            return False, QueryRelevanceDiagnostics(
                query_id=intent.query_id,
                canonical_query=intent.original_query,
                target_language=lang,
                relevance_score=0.0,
                is_accepted=False,
                stage="STAGE_2_CONTENT",
                rejection_reason="Article content too short (< 80 chars)",
                reasons=["Insufficient body content"]
            )

        # 1. Topic Keyword Matching in Body (Multilingual + English fallback)
        topic_kws = (
            intent.topic_keywords.get(lang, []) +
            intent.topic_keywords.get("en", []) +
            [intent.topic.lower()]
        )
        matched_topic_terms = [kw for kw in topic_kws if kw and kw in full_lower]
        topic_match = len(matched_topic_terms) > 0
        if topic_match:
            reasons.append(f"Topic matched terms: {matched_topic_terms[:3]}")

        # 2. Event / Action Keyword Matching in Body
        matched_event_terms = []
        if intent.event:
            action_kws = (
                intent.action_keywords.get(lang, []) +
                intent.action_keywords.get("en", []) +
                [intent.event.lower()]
            )
            matched_event_terms = [ak for ak in action_kws if ak and ak in full_lower]
            event_match = len(matched_event_terms) > 0
            if event_match:
                reasons.append(f"Event matched terms: {matched_event_terms[:3]}")
        else:
            event_match = True

        # 3. Co-occurrence in Sentence/Paragraph Window
        cooccurrence_match = False
        if topic_match and event_match and intent.event:
            sentences = re.split(r'[।॥\.\n\?!]+', text_norm)
            for s in sentences:
                s_lower = s.lower()
                has_top = any(t in s_lower for t in matched_topic_terms)
                has_evt = any(e in s_lower for e in matched_event_terms)
                if has_top and has_evt:
                    cooccurrence_match = True
                    reasons.append(f"Semantic co-occurrence verified in sentence: '{s[:70]}...'")
                    break
        elif not intent.event:
            cooccurrence_match = True

        # 4. Temporal Validation (Year & Date)
        date_match = True
        temporal_context = f"{title_norm} {text_norm[:3000]} {pub_date} {url}"
        extracted_years = cls.extract_years_and_dates(temporal_context)
        
        if intent.year:
            if intent.year in extracted_years or str(intent.year) in str(pub_date) or str(intent.year) in url:
                date_match = True
                reasons.append(f"Verified requested year {intent.year} in article context/metadata")
            elif extracted_years and all(y < intent.year for y in extracted_years) and not (str(intent.year) in str(pub_date)):
                # Article only discusses older historical years (e.g. [2021, 2022] when 2026 requested)
                date_match = False
                reasons.append(f"Temporal rejection: Article only discusses historical years {extracted_years}")
            else:
                # Year not explicitly mentioned in short text, but no older year contradiction
                date_match = True
                reasons.append(f"No conflicting past years found; temporal match assumed for current cycle")

        # 5. Entity Disambiguation (e.g. Reject "President visits" when "Vice President visits" requested)
        if "vice president" in intent.original_query.lower():
            if "president" in full_lower and "vice president" not in full_lower and "துணை" not in full_lower and "उप" not in full_lower:
                return False, QueryRelevanceDiagnostics(
                    query_id=intent.query_id,
                    canonical_query=intent.original_query,
                    target_language=lang,
                    relevance_score=0.15,
                    is_accepted=False,
                    stage="STAGE_2_CONTENT",
                    rejection_reason="Entity mismatch: Article discusses President instead of Vice President",
                    reasons=["Article lacks Vice President context"]
                )

        # 6. Compute Stage 2 Composite Relevance Score
        topic_score = 0.35 if topic_match else 0.0
        event_score = 0.25 if event_match else (0.15 if not intent.event else 0.0)
        cooc_score = 0.20 if cooccurrence_match else 0.0
        date_score = 0.20 if date_match else 0.0

        source_bonus = 1.15 if any(auth in url.lower() for auth in cls.AUTHORITATIVE_DOMAINS) else 1.0
        base_score = topic_score + event_score + cooc_score + date_score
        final_score = min(1.0, round(base_score * source_bonus, 3))

        # Precision Rule: Must match Topic, Event, Co-occurrence (if event specified), and Date
        is_accepted = (final_score >= min_threshold) and topic_match and (event_match or not intent.event) and (cooccurrence_match or not intent.event) and date_match

        rejection = None
        if not is_accepted:
            if not topic_match:
                rejection = f"Article body lacks core topic '{intent.topic}'"
            elif not event_match:
                rejection = f"Article body lacks event '{intent.event}'"
            elif not cooccurrence_match and intent.event:
                rejection = f"Topic and event do not co-occur in any context paragraph"
            elif not date_match:
                rejection = f"Article does not match target year {intent.year}"
            else:
                rejection = f"Deep relevance score ({final_score:.2f}) below threshold ({min_threshold})"

        diagnostics = QueryRelevanceDiagnostics(
            query_id=intent.query_id,
            canonical_query=intent.original_query,
            target_language=lang,
            relevance_score=final_score,
            is_accepted=is_accepted,
            stage="STAGE_2_CONTENT",
            topic_match=topic_match,
            event_match=event_match,
            date_match=date_match,
            cooccurrence_match=cooccurrence_match,
            extracted_year=extracted_years[0] if extracted_years else None,
            extracted_pub_date=pub_date,
            is_temporal_valid=date_match,
            reasons=reasons,
            rejection_reason=rejection,
            source_quality_score=source_bonus
        )

        return is_accepted, diagnostics
