"""
Direct Debugging Script for AsyncSearchEngine & Live Providers.
Tests raw search, HTML/RSS responses, exception handling, and parsing for:
- English (en)
- Tamil (ta)
- Hindi (hi)
- Marathi (mr)
"""

import sys
import os
import asyncio
import traceback
from pathlib import Path

# Force UTF-8 for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.async_search_engine import AsyncSearchEngine
from app.crawlers.query_intent import QueryIntentAnalyzer
from app.crawlers.topic_filter import TopicRelevanceFilter


async def debug_search():
    crawler = AsyncCrawler(max_concurrent_requests=10, timeout=10.0)
    engine = AsyncSearchEngine(crawler)

    query = "vice president visit 2026"
    print("=" * 70)
    print(f"STEP 1: ANALYZING QUERY INTENT FOR '{query}'")
    print("=" * 70)
    intent = QueryIntentAnalyzer.analyze_query(query)
    print(f"Topic: {intent.topic}")
    print(f"Event: {intent.event}")
    print(f"Year:  {intent.year}")
    print("Multilingual Queries:")
    for lang, q_list in intent.multilingual_queries.items():
        print(f"  [{lang.upper()}]: {q_list}")

    print("\n" + "=" * 70)
    print("STEP 2: TESTING INDIVIDUAL SEARCH PROVIDERS DIRECTLY (NO FILTER)")
    print("=" * 70)

    test_queries = {
        "en": intent.multilingual_queries["en"][0] if intent.multilingual_queries.get("en") else query,
        "ta": intent.multilingual_queries["ta"][0] if intent.multilingual_queries.get("ta") else "குடியரசு துணைத் தலைவர் பயணம் 2026",
        "hi": intent.multilingual_queries["hi"][0] if intent.multilingual_queries.get("hi") else "उपराष्ट्रपति दौरा 2026",
        "mr": intent.multilingual_queries["mr"][0] if intent.multilingual_queries.get("mr") else "उपराष्ट्रपती दौरा 2026"
    }

    for lang, lang_q in test_queries.items():
        print(f"\n------------------------------------------------------------")
        print(f"[{lang.upper()}] Testing Query: '{lang_q}'")
        print(f"------------------------------------------------------------")

        # Test Google News RSS
        try:
            gn_results = await engine._search_google_news_rss(lang_q, language=lang, max_results=10)
            print(f"  Google News RSS:  {len(gn_results)} results")
            for r in gn_results[:3]:
                print(f"    - Title: {r.get('title', '')[:60]} | URL: {r.get('url', '')[:60]}")
        except Exception as e:
            print(f"  Google News RSS ERROR: {e}")
            traceback.print_exc()

        # Test Bing News
        try:
            bn_results = await engine._search_bing_news(lang_q, language=lang, max_results=10)
            print(f"  Bing News:        {len(bn_results)} results")
            for r in bn_results[:3]:
                print(f"    - Title: {r.get('title', '')[:60]} | URL: {r.get('url', '')[:60]}")
        except Exception as e:
            print(f"  Bing News ERROR: {e}")

        # Test Bing Web
        try:
            bw_results = await engine._search_bing_web(lang_q, language=lang, max_results=10)
            print(f"  Bing Web:         {len(bw_results)} results")
            for r in bw_results[:3]:
                print(f"    - Title: {r.get('title', '')[:60]} | URL: {r.get('url', '')[:60]}")
        except Exception as e:
            print(f"  Bing Web ERROR: {e}")

        # Test Wikipedia
        try:
            wiki_results = await engine._search_wikipedia_async(lang_q, language=lang, max_results=5)
            print(f"  Wikipedia:        {len(wiki_results)} results")
            for r in wiki_results[:2]:
                print(f"    - Title: {r.get('title', '')[:60]} | URL: {r.get('url', '')[:60]}")
        except Exception as e:
            print(f"  Wikipedia ERROR: {e}")

        # Test Direct Feeds
        try:
            feed_results = await engine._search_direct_feeds(lang_q, language=lang, max_results=10)
            print(f"  Direct Feeds:     {len(feed_results)} results")
            for r in feed_results[:2]:
                print(f"    - Title: {r.get('title', '')[:60]} | URL: {r.get('url', '')[:60]}")
        except Exception as e:
            print(f"  Direct Feeds ERROR: {e}")

        # Test full search_by_intent
        print(f"\n  >> Running search_by_intent for [{lang.upper()}]...")
        accepted, rejected = await engine.search_by_intent(
            intent=intent,
            language=lang,
            max_results=15,
            min_stage1_threshold=0.35
        )
        print(f"  >> search_by_intent: {len(accepted)} accepted, {len(rejected)} rejected")
        for acc in accepted[:3]:
            print(f"     [ACCEPTED] Score: {acc.get('relevance_score'):.2f} | {acc.get('title', '')[:60]} | {acc.get('url', '')[:60]}")
        for rej in rejected[:3]:
            diag = rej.get('stage1_diagnostics', {})
            print(f"     [REJECTED] Reason: {diag.get('rejection_reason')} | {rej.get('title', '')[:60]}")

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(debug_search())
