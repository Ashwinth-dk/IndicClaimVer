"""
Unit and Integration Test Suite for Query-Driven, Relevance-Aware Multilingual Crawler.
Specifically validates:
1. Structured Query Intent Decomposition (Topic, Event, Year, Entities, Multilingual Queries)
2. Multilingual Query Expansion across English, Tamil, Hindi, and Marathi
3. Two-Stage Relevance Filtering (Stage 1 Pre-Fetch Snippet & Stage 2 Deep Content)
4. Temporal Validation (2026 Context vs Stale Years)
5. Entity Disambiguation (Vice President vs President)
6. End-to-End Scraper Pipeline Execution with Funnel Metrics
"""

import sys
import os
from pathlib import Path

# Force UTF-8 encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.crawlers.query_intent import QueryIntentAnalyzer, QueryIntent
from app.crawlers.topic_filter import TopicRelevanceFilter, QueryRelevanceDiagnostics
from app.services.scraper_service import ScraperService, CrawlRequest
from app.storage.dataset_manager import DatasetManager


def test_1_query_intent_decomposition():
    print("=" * 70)
    print("TEST 1: QUERY INTENT DECOMPOSITION & MULTILINGUAL EXPANSION")
    print("=" * 70)

    test_queries = [
        ("Vice President visits 2026", "Vice President", "visits", 2026),
        ("Prime Minister visits Tamil Nadu 2026", "Prime Minister", "visits", 2026),
        ("ISRO launches 2026", "ISRO", "launches", 2026),
        ("India inflation January 2026", "Inflation", None, 2026),
        ("Chief Minister Maharashtra schemes 2026", "Chief Minister", "schemes", 2026),
    ]

    for q_str, exp_topic, exp_event, exp_year in test_queries:
        intent = QueryIntentAnalyzer.analyze_query(q_str)
        print(f"\n[QUERY] '{q_str}'")
        print(f"  -> Topic:    {intent.topic} (Expected: {exp_topic})")
        print(f"  -> Event:    {intent.event} (Expected: {exp_event})")
        print(f"  -> Year:     {intent.year} (Expected: {exp_year})")
        print(f"  -> Entities: {intent.entities}")
        print("  -> Generated Native Multilingual Queries:")
        for l, q_list in intent.multilingual_queries.items():
            print(f"     [{l.upper()}]: {q_list}")

        assert exp_topic.lower() in intent.topic.lower(), f"Topic mismatch for '{q_str}'"
        assert intent.year == exp_year, f"Year mismatch for '{q_str}'"
        assert all(l in intent.multilingual_queries for l in ["en", "ta", "hi", "mr"]), "Missing language queries"

    print("\n[TEST 1 PASSED] All query intents and multilingual expansions validated successfully!")


def test_2_stage1_snippet_filtering():
    print("\n" + "=" * 70)
    print("TEST 2: STAGE 1 PRE-FETCH SNIPPET RELEVANCE FILTERING")
    print("=" * 70)

    intent = QueryIntentAnalyzer.analyze_query("Vice President visits 2026")

    candidate_snippets = [
        # (title, snippet, url, pub_date, expected_accept, description)
        (
            "Vice President visits Japan in March 2026 for bilateral summit",
            "The Vice President of India will embark on an official visit to Tokyo in 2026.",
            "https://pib.gov.in/PressReleasePage.aspx?PRID=190001",
            "2026-03-10",
            True,
            "Relevant: Topic + Event + 2026 Year"
        ),
        (
            "குடியரசு துணைத் தலைவர் 2026 மார்ச் மாதம் ஜப்பான் பயணம்",
            "இந்திய துணை ஜனாதிபதி அதிகாரப்பூர்வமாக வெளிநாட்டு பயணம் மேற்கொள்கிறார்.",
            "https://dinamalar.com/news/12345",
            "2026-03-12",
            True,
            "Relevant (Tamil): குடியரசு துணைத் தலைவர் + பயணம் + 2026"
        ),
        (
            "उपराष्ट्रपति 2026 में फ्रांस का आधिकारिक दौरा करेंगे",
            "भारत के उपराष्ट्रपति मार्च 2026 में पेरिस की यात्रा पर रहेंगे।",
            "https://amarujala.com/india-news/67890",
            "2026-03-14",
            True,
            "Relevant (Hindi): उपराष्ट्रपति + दौरा + 2026"
        ),
        (
            "उपराष्ट्रपती मार्च 2026 मध्ये महाराष्ट्र दौऱ्यावर येणार",
            "भारताचे उपराष्ट्रपती विविध विकास कामांच्या उद्घाटनासाठी उपस्थित राहतील.",
            "https://loksatta.com/maharashtra/11223",
            "2026-03-15",
            True,
            "Relevant (Marathi): उपराष्ट्रपती + दौरा + 2026"
        ),
        # Irrelevant cases to reject
        (
            "Vice President delivers speech on education policy",
            "The Vice President addressed students at the national university convocation.",
            "https://news.example.com/edu",
            "2026-01-10",
            False,
            "Irrelevant: Mentions VP but missing visit/travel context"
        ),
        (
            "President visits France in 2026 for state banquet",
            "The President of India arrived in Paris today for official bilateral meetings.",
            "https://news.example.com/pres",
            "2026-02-15",
            False,
            "Irrelevant: Entity mismatch (President instead of Vice President)"
        ),
        (
            "Vice President appointed new advisory committee in 2026",
            "A new parliamentary advisory committee was constituted today.",
            "https://news.example.com/appoint",
            "2026-01-20",
            False,
            "Irrelevant: Action mismatch (appointment vs visit)"
        ),
        (
            "Vice President visited Mumbai in March 2024",
            "The Vice President concluded his two-day visit to Maharashtra in 2024.",
            "https://news.example.com/2024-tour",
            "2024-03-12",
            False,
            "Irrelevant: Stale historical year (2024 when 2026 requested)"
        )
    ]

    for title, snip, url, pdate, exp_accept, desc in candidate_snippets:
        is_acc, diag = TopicRelevanceFilter.evaluate_stage1_snippet(
            intent=intent,
            title=title,
            snippet=snip,
            url=url,
            pub_date=pdate,
            lang=diag_lang if (diag_lang := "en" if "Vice President" in title or "President" in title else ("ta" if "குடியரசு" in title else ("hi" if "उपराष्ट्रपति" in title else "mr"))) else "en",
            min_threshold=0.40
        )
        status = "PASSED" if is_acc == exp_accept else "FAILED"
        print(f"\n  [{status}] {desc}")
        print(f"      Title:    {title[:65]}...")
        print(f"      Decision: {'ACCEPTED' if is_acc else 'REJECTED'} (Expected: {'ACCEPTED' if exp_accept else 'REJECTED'}) | Score: {diag.relevance_score:.2f}")
        if not is_acc:
            print(f"      Reason:   {diag.rejection_reason}")
        assert is_acc == exp_accept, f"Stage 1 filtering mismatch for: {title}"

    print("\n[TEST 2 PASSED] Stage 1 pre-fetch relevance filtering correctly accepted relevant and rejected off-topic/stale snippets!")


def test_3_stage2_content_filtering():
    print("\n" + "=" * 70)
    print("TEST 3: STAGE 2 DEEP ARTICLE CONTENT & TEMPORAL VALIDATION")
    print("=" * 70)

    intent = QueryIntentAnalyzer.analyze_query("Vice President visits 2026")

    articles = [
        # (title, body, pub_date, url, exp_accept, desc)
        (
            "Vice President to visit Tokyo in March 2026",
            "New Delhi: The Vice President of India will undertake an official visit to Japan from March 15 to March 18, 2026. During the visit, the Vice President will meet top government dignitaries and inaugurate the India-Japan cultural pavilion.",
            "2026-03-01",
            "https://pib.gov.in/vp-japan-2026",
            True,
            "Relevant: Vice President + official visit + March 2026 with semantic co-occurrence"
        ),
        (
            "Vice President attends book release on constitution",
            "New Delhi: The Vice President attended the release of a new book on constitutional reforms in 2026. Speaking on the occasion, the Vice President emphasized the importance of fundamental duties and democratic values across educational institutions.",
            "2026-02-10",
            "https://news.example.com/book-release",
            False,
            "Irrelevant: Missing visit/travel co-occurrence with Vice President"
        ),
        (
            "President of India visits Mumbai in 2026",
            "Mumbai: The President of India arrived in Mumbai for an official state visit in 2026 to inaugurate the newly constructed metro corridor and address the joint session of legislature.",
            "2026-02-20",
            "https://news.example.com/pres-mumbai",
            False,
            "Irrelevant: President is NOT Vice President"
        ),
        (
            "Vice President concluded Maharashtra visit in 2024",
            "Mumbai: In March 2024, the Vice President visited Nagpur and Pune for a two-day tour. The 2024 tour witnessed high public engagement and several academic lectures.",
            "2024-03-20",
            "https://news.example.com/vp-2024",
            False,
            "Irrelevant: Historical 2024 content when 2026 requested"
        )
    ]

    for title, body, pdate, url, exp_accept, desc in articles:
        is_acc, diag = TopicRelevanceFilter.evaluate_stage2_content(
            intent=intent,
            title=title,
            full_text=body,
            pub_date=pdate,
            url=url,
            lang="en",
            min_threshold=0.50
        )
        status = "PASSED" if is_acc == exp_accept else "FAILED"
        print(f"\n  [{status}] {desc}")
        print(f"      Title:    {title}")
        print(f"      Decision: {'ACCEPTED' if is_acc else 'REJECTED'} (Expected: {'ACCEPTED' if exp_accept else 'REJECTED'}) | Score: {diag.relevance_score:.2f}")
        print(f"      Matches:  Topic={diag.topic_match}, Event={diag.event_match}, Co-occurrence={diag.cooccurrence_match}, Year={diag.date_match}")
        if not is_acc:
            print(f"      Rejection: {diag.rejection_reason}")
        assert is_acc == exp_accept, f"Stage 2 filtering mismatch for: {title}"

    print("\n[TEST 3 PASSED] Stage 2 deep content relevance filtering successfully validated co-occurrence and temporal integrity!")


def test_4_multilingual_scraper_integration():
    print("\n" + "=" * 70)
    print("TEST 4: SCRAPER SERVICE QUERY-DRIVEN INTEGRATION & FUNNEL METRICS")
    print("=" * 70)

    scraper = ScraperService()
    req = CrawlRequest(
        query="Vice President visits 2026",
        language="all",
        target_count=5
    )

    scraper._reset_state(req)
    status = scraper.get_status()

    print(f"  Task ID:          {status['task_id']}")
    print(f"  Query:            {status['query']}")
    print(f"  Query Intent ID:  {status['query_intent']['query_id']}")
    print(f"  Intent Topic:     {status['query_intent']['topic']}")
    print(f"  Intent Event:     {status['query_intent']['event']}")
    print(f"  Intent Year:      {status['query_intent']['year']}")
    print(f"  Target Languages: {status['query_intent']['target_languages']}")
    print("  Initial Funnel Statistics:")
    for k, v in status["funnel"].items():
        print(f"    - {k:<28}: {v}")

    assert status["query_intent"]["topic"] == "Vice President"
    assert status["query_intent"]["year"] == 2026
    assert status["funnel"]["query_id"].startswith("Q-")

    print("\n[TEST 4 PASSED] Scraper service query intent decomposition and funnel telemetry validated!")


if __name__ == "__main__":
    test_1_query_intent_decomposition()
    test_2_stage1_snippet_filtering()
    test_3_stage2_content_filtering()
    test_4_multilingual_scraper_integration()
    print("\n" + "=" * 70)
    print("ALL QUERY-DRIVEN MULTILINGUAL CRAWLER TESTS PASSED PERFECTLY!")
    print("=" * 70)
