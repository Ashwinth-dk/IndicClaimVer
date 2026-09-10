"""
Query Intent Analyzer & Multilingual Query Expansion.
Decomposes user research queries into structured intent (topic, event/action,
temporal constraints, entities, target languages) and generates native,
high-precision search queries for English, Tamil, Hindi, and Marathi.
"""

import re
import uuid
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from app.utils.language_detector import LanguageDetector


class QueryIntent(BaseModel):
    """Structured representation of user research query intent."""
    query_id: str = Field(default_factory=lambda: f"Q-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}")
    original_query: str
    topic: str
    event: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None
    temporal_qualifier: Optional[str] = None
    entities: List[str] = Field(default_factory=list)
    target_languages: List[str] = Field(default_factory=lambda: ["en", "ta", "hi", "mr"])
    source_categories: List[str] = Field(default_factory=lambda: ["fact_check", "news", "official"])
    
    # Generated native multilingual search queries
    multilingual_queries: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Structured keywords for precise two-stage relevance checking
    topic_keywords: Dict[str, List[str]] = Field(default_factory=dict)
    action_keywords: Dict[str, List[str]] = Field(default_factory=dict)
    temporal_keywords: List[str] = Field(default_factory=list)
    relevance_keywords: Dict[str, List[str]] = Field(default_factory=dict)


class QueryIntentAnalyzer:
    """
    Analyzes natural language queries and decomposes them into structured intent
    with native multilingual query expansions for EN, TA, HI, MR.
    """

    # Common entities and cross-lingual mappings
    ENTITY_MAPPINGS = {
        "vice president": {
            "en": ["Vice President", "Vice-President", "Vice President of India", "VP", "VP Radhakrishnan", "C.P. Radhakrishnan", "Jagdeep Dhankhar"],
            "ta": ["குடியரசு துணைத் தலைவர்", "குடியரசுத் துணைத் தலைவர்", "துணை ஜனாதிபதி", "துணைத் தலைவர்", "துணைத்தலைவர்", "ராதாகிருஷ்ணன்"],
            "hi": ["उपराष्ट्रपति", "उप-राष्ट्रपति", "भारत के उपराष्ट्रपति", "राधाकृष्णन", "जगदीप धनखड़"],
            "mr": ["उपराष्ट्रपती", "भारताचे उपराष्ट्रपती", "उप-राष्ट्रपती", "उपराष्ट्रपतींनी", "उपराष्ट्रपतींच्या", "राधाकृष्णन"]
        },
        "prime minister": {
            "en": ["Prime Minister", "PM Modi", "PM", "Prime Minister Modi", "Narendra Modi"],
            "ta": ["பிரதமர்", "பிரதம மந்திரி", "பிரதமர் மோடி", "நரேந்திர மோடி"],
            "hi": ["प्रधानमंत्री", "पीएम मोदी", "प्रधानमंत्री मोदी", "नरेंद्र मोदी"],
            "mr": ["पंतप्रधान", "पंतप्रधान मोदी", "नरेंद्र मोदी"]
        },
        "president": {
            "en": ["President of India", "President Droupadi Murmu", "Rashtrapati", "President Murmu"],
            "ta": ["குடியரசுத் தலைவர்", "ஜனாதிபதி", "திரௌபதி முர்மு"],
            "hi": ["राष्ट्रपति", "भारत के राष्ट्रपति", "द्रौपदी मुर्मू", "राष्ट्रपति मुर्मू"],
            "mr": ["राष्ट्रपती", "भारताचे राष्ट्रपती", "द्रौपदी मुर्मू"]
        },
        "chief minister": {
            "en": ["Chief Minister", "CM"],
            "ta": ["முதலமைச்சர்", "முதல்வர்"],
            "hi": ["मुख्यमंत्री", "सीएम"],
            "mr": ["मुख्यमंत्री", "ना. मुख्यमंत्री"]
        },
        "isro": {
            "en": ["ISRO", "Indian Space Research Organisation"],
            "ta": ["இஸ்ரோ", "இந்திய விண்வெளி ஆய்வு மையம்"],
            "hi": ["इसरो", "भारतीय अंतरिक्ष अनुसंधान संगठन"],
            "mr": ["इस्रो", "भारतीय अंतराळ संशोधन संस्था"]
        },
        "supreme court": {
            "en": ["Supreme Court", "CJI", "Apex Court"],
            "ta": ["உச்ச நீதிமன்றம்", "உச்சநீதிமன்றம்"],
            "hi": ["सुप्रीम कोर्ट", "सर्वोच्च न्यायालय"],
            "mr": ["सर्वोच्च न्यायालय", "सुप्रीम कोर्ट"]
        },
        "election commission": {
            "en": ["Election Commission of India", "ECI", "Chief Election Commissioner"],
            "ta": ["தேர்தல் ஆணையம்", "இந்திய தேர்தல் ஆணையம்"],
            "hi": ["चुनाव आयोग", "भारतीय निर्वाचन आयोग"],
            "mr": ["निवडणूक आयोग", "भारतीय निवडणूक आयोग"]
        },
        "rbi": {
            "en": ["RBI", "Reserve Bank of India"],
            "ta": ["ரிசர்வ் வங்கி", "இந்திய ரிசர்வ் வங்கி"],
            "hi": ["आरबीआई", "भारतीय रिजर्व बैंक"],
            "mr": ["रिझर्व्ह बँक", "भारतीय रिझर्व्ह बँक"]
        },
        "inflation": {
            "en": ["inflation", "CPI inflation", "retail inflation", "price rise"],
            "ta": ["பணவீக்கம்", "விலைவாசி உயர்வு"],
            "hi": ["मुद्रास्फीति", "महंगाई", "खुदरा मुद्रास्फीति"],
            "mr": ["महागाई", "किरकोळ महागाई दर"]
        },
        "budget": {
            "en": ["Union Budget", "Budget 2026", "Finance Ministry"],
            "ta": ["மத்திய பட்ஜெட்", "பட்ஜெட்"],
            "hi": ["केंद्रीय बजट", "आम बजट"],
            "mr": ["केंद्रीय अर्थसंकल्प", "अर्थसंकल्प"]
        }
    }

    # Action / Event mappings across languages
    ACTION_MAPPINGS = {
        "visit": {
            "en": ["visit", "visits", "visiting", "visited", "official visit", "tour", "touring", "tours", "travelled", "travelling", "travels", "arrived", "arrives", "inaugurated", "inauguration", "unveiled", "delegation"],
            "ta": ["பயணம்", "பயணத்தை", "பயணத்தின்", "வருகை", "வருகிறார்", "வருகை தந்தார்", "அதிகாரப்பூர்வ பயணம்", "தொடங்கி வைத்தார்", "சென்றார்", "பார்வையிட்டார்", "பங்கேற்றார்"],
            "hi": ["दौरा", "दौरे", "दौरों", "दौरे पर", "यात्रा", "यात्राएं", "आधिकारिक यात्रा", "उद्घाटन", "पहुंचे", "पहुंचेंगे", "मुलाकात", "भेंट"],
            "mr": ["दौरा", "दौऱ्यावर", "दौऱ्याची", "भेट", "भेटी", "भेटीची", "भेटीसाठी", "अधिकृत भेट", "उद्घाटन", "उपस्थिती", "पोहचले", "मुलाखत"]
        },
        "launch": {
            "en": ["launch", "launches", "inaugurate", "unveil", "introduced", "mission"],
            "ta": ["ஏவுதல்", "தொடங்கி வைத்தார்", "அறிமுகம்", "திட்டம் தொடக்கம்"],
            "hi": ["लॉन्च", "शुरुआत", "उद्घाटन", "शुरू किया", "मिशन"],
            "mr": ["प्रक्षेपण", "सुरू", "उद्घाटन", "लोकार्पण", "मोहीम"]
        },
        "scheme": {
            "en": ["scheme", "schemes", "welfare scheme", "subsidy", "initiative", "announcement", "yojana"],
            "ta": ["திட்டம்", "திட்டங்கள்", "நலத்திட்டம்", "அறிவிப்பு"],
            "hi": ["योजना", "योजनाएं", "कल्याणकारी योजना", "घोषणा", "पहल"],
            "mr": ["योजना", "योजनांचा", "कल्याणकारी योजना", "घोषणा", "उपक्रम"]
        },
        "election": {
            "en": ["election", "elections", "polls", "voting", "assembly election"],
            "ta": ["தேர்தல்", "வாக்குப்பதிவு", "சட்டமன்ற தேர்தல்"],
            "hi": ["चुनाव", "मतदान", "विधानसभा चुनाव"],
            "mr": ["निवडणूक", "मतदान", "विधानसभा निवडणूक"]
        },
        "statement": {
            "en": ["statement", "announced", "clarified", "claims", "decision"],
            "ta": ["அறிவிப்பு", "விளக்கம்", "கூறியுள்ளார்"],
            "hi": ["बयान", "घोषणा", "स्पष्टीकरण", "कहा"],
            "mr": ["विधान", "घोषणा", "स्पष्टीकरण", "म्हटले"]
        }
    }

    # Location mappings
    LOCATION_MAPPINGS = {
        "tamil nadu": {"en": "Tamil Nadu", "ta": "தமிழ்நாடு", "hi": "तमिलनाडु", "mr": "तमिळनाडू"},
        "maharashtra": {"en": "Maharashtra", "ta": "மகாராஷ்டிரா", "hi": "महाराष्ट्र", "mr": "महाराष्ट्र"},
        "delhi": {"en": "Delhi", "ta": "டெல்லி", "hi": "दिल्ली", "mr": "दिल्ली"},
        "uttar pradesh": {"en": "Uttar Pradesh", "ta": "உத்தரப் பிரதேசம்", "hi": "उत्तर प्रदेश", "mr": "उत्तर प्रदेश"},
        "kerala": {"en": "Kerala", "ta": "கேரளா", "hi": "केरल", "mr": "केरळ"},
        "karnataka": {"en": "Karnataka", "ta": "கர்நாடகா", "hi": "कर्नाटक", "mr": "कर्नाटक"},
        "japan": {"en": "Japan", "ta": "ஜப்பான்", "hi": "जापान", "mr": "जपान"},
        "france": {"en": "France", "ta": "பிரான்ஸ்", "hi": "फ्रांस", "mr": "फ्रान्स"},
        "india": {"en": "India", "ta": "இந்தியா", "hi": "भारत", "mr": "भारत"}
    }

    MONTH_NAMES = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9, "oct": 10, "nov": 11, "dec": 12
    }

    @classmethod
    def analyze_query(
        cls,
        query: str,
        target_languages: Optional[List[str]] = None,
        max_queries_per_lang: int = 6
    ) -> QueryIntent:
        """
        Decomposes a research query into structured intent and generates native multilingual search queries.
        """
        query_norm = unicodedata.normalize("NFC", query.strip())
        lower_query = query_norm.lower()
        langs = target_languages or ["en", "ta", "hi", "mr"]

        # 1. Extract Year & Temporal Qualifiers
        year = None
        year_match = re.search(r"\b(20[1-3][0-9])\b", lower_query)
        if year_match:
            year = int(year_match.group(1))

        month = None
        for m_name, m_num in cls.MONTH_NAMES.items():
            if re.search(rf"\b{m_name}\b", lower_query):
                month = m_num
                break

        temporal_qualifier = None
        for tq in ["latest", "recent", "today", "yesterday", "this week", "this month"]:
            if tq in lower_query:
                temporal_qualifier = tq
                break

        # 2. Extract Entities & Locations
        matched_entities = []
        topic_key = None
        topic_str = ""

        # Check predefined entity mappings
        for key in cls.ENTITY_MAPPINGS:
            if key in lower_query:
                topic_key = key
                topic_str = cls.ENTITY_MAPPINGS[key]["en"][0]
                matched_entities.append(topic_str)
                break

        # Check locations
        matched_locations = {}
        for loc_key, loc_dict in cls.LOCATION_MAPPINGS.items():
            if loc_key in lower_query:
                matched_locations[loc_key] = loc_dict
                matched_entities.append(loc_dict["en"])

        # 3. Extract Action / Event
        action_key = None
        event_str = None
        for act_k in cls.ACTION_MAPPINGS:
            for variant in cls.ACTION_MAPPINGS[act_k]["en"]:
                if re.search(rf"\b{re.escape(variant)}\b", lower_query):
                    action_key = act_k
                    event_str = variant
                    break
            if action_key:
                break

        # Fallback if topic is still empty: strip year, action, month, and use remainder
        if not topic_str:
            clean_topic = lower_query
            if year:
                clean_topic = clean_topic.replace(str(year), "")
            if event_str:
                clean_topic = clean_topic.replace(event_str, "")
            for m_name in cls.MONTH_NAMES:
                clean_topic = re.sub(rf"\b{m_name}\b", "", clean_topic)
            clean_topic = re.sub(r"\s+", " ", clean_topic).strip()
            topic_str = clean_topic.title() if clean_topic else query_norm

        # Separate Topic vs Action vs Temporal Keywords
        topic_kws: Dict[str, List[str]] = {}
        action_kws: Dict[str, List[str]] = {}
        temp_kws: List[str] = [str(year)] if year else []
        if month:
            temp_kws.append(str(month))

        for lang in ["en", "ta", "hi", "mr"]:
            # Topic terms only
            t_set = set()
            if topic_key and topic_key in cls.ENTITY_MAPPINGS:
                for term in cls.ENTITY_MAPPINGS[topic_key].get(lang, []):
                    t_set.add(term.lower())
            else:
                t_set.add(topic_str.lower())
            # Add locations
            for loc_dict in matched_locations.values():
                if lang in loc_dict:
                    t_set.add(loc_dict[lang].lower())
            topic_kws[lang] = list(t_set)

            # Action terms only
            a_set = set()
            if action_key and action_key in cls.ACTION_MAPPINGS:
                for term in cls.ACTION_MAPPINGS[action_key].get(lang, []):
                    a_set.add(term.lower())
            elif event_str:
                a_set.add(event_str.lower())
            action_kws[lang] = list(a_set)

        intent = QueryIntent(
            original_query=query_norm,
            topic=topic_str,
            event=event_str or action_key,
            year=year,
            month=month,
            temporal_qualifier=temporal_qualifier,
            entities=matched_entities,
            target_languages=langs,
            topic_keywords=topic_kws,
            action_keywords=action_kws,
            temporal_keywords=temp_kws
        )

        # 4. Generate native multilingual queries
        intent.multilingual_queries = cls._generate_multilingual_queries(
            intent=intent,
            topic_key=topic_key,
            action_key=action_key,
            matched_locations=matched_locations,
            max_queries=max_queries_per_lang
        )

        return intent

    @classmethod
    def _generate_multilingual_queries(
        cls,
        intent: QueryIntent,
        topic_key: Optional[str],
        action_key: Optional[str],
        matched_locations: Dict[str, Dict[str, str]],
        max_queries: int = 6
    ) -> Dict[str, List[str]]:
        """Generates language-specific targeted search queries for each supported language."""
        queries: Dict[str, List[str]] = {}
        year_str = str(intent.year) if intent.year else ""

        for lang in intent.target_languages:
            lang_q_list = []

            # 1. Canonical query in target language if we have entity & action mappings
            if topic_key and topic_key in cls.ENTITY_MAPPINGS:
                topic_variants = cls.ENTITY_MAPPINGS[topic_key].get(lang, cls.ENTITY_MAPPINGS[topic_key]["en"])
                action_variants = cls.ACTION_MAPPINGS.get(action_key, {}).get(lang, [""]) if action_key else [""]
                
                # Location variant
                loc_terms = [loc_dict.get(lang, loc_dict["en"]) for loc_dict in matched_locations.values()]
                loc_part = " ".join(loc_terms)

                # 1. Topic + Action combinations (highest precision & relevance)
                for t_var in topic_variants[:2]:
                    for a_var in action_variants[:2]:
                        parts = [t_var]
                        if loc_part:
                            parts.append(loc_part)
                        if a_var:
                            parts.append(a_var)
                        
                        q_broad = " ".join(p for p in parts if p).strip()
                        if q_broad and q_broad not in lang_q_list:
                            lang_q_list.append(q_broad)

                        if year_str:
                            q_year = f"{q_broad} {year_str}".strip()
                            if q_year not in lang_q_list:
                                lang_q_list.append(q_year)

                # 2. Regional / Entity combinations
                if lang == "mr":
                    for extra in ["उपराष्ट्रपती राधाकृष्णन", "उपराष्ट्रपती महाराष्ट्र", "उपराष्ट्रपती भेट", "उपराष्ट्रपती दौरा", "भारताचे उपराष्ट्रपती"]:
                        if extra not in lang_q_list:
                            lang_q_list.append(extra)
                elif lang == "ta":
                    for extra in ["குடியரசு துணைத் தலைவர் ராதாகிருஷ்ணன்", "குடியரசு துணைத் தலைவர் தமிழ்நாடு", "துணை ஜனாதிபதி வருகை", "குடியரசுத் துணைத் தலைவர்"]:
                        if extra not in lang_q_list:
                            lang_q_list.append(extra)
                elif lang == "hi":
                    for extra in ["उपराष्ट्रपति राधाकृष्णन", "उपराष्ट्रपति दौरा", "भारत के उपराष्ट्रपति", "उपराष्ट्रपति यात्रा"]:
                        if extra not in lang_q_list:
                            lang_q_list.append(extra)

                # 3. Standalone topic entities (fallback high recall)
                for t_var in topic_variants[:3]:
                    if t_var not in lang_q_list:
                        lang_q_list.append(t_var)
            else:
                det_lang = LanguageDetector.detect_language(intent.original_query)["language"]
                if det_lang == lang or lang == "en":
                    lang_q_list.append(intent.original_query)
                else:
                    q_str = f"{intent.topic} {year_str}".strip()
                    lang_q_list.append(q_str)

            queries[lang] = lang_q_list[:max_queries]

        return queries
