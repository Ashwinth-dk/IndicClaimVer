import asyncio
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.async_search_engine import AsyncSearchEngine
from app.crawlers.query_intent import QueryIntentAnalyzer
from app.crawlers.topic_filter import TopicRelevanceFilter
from app.extractors.claim_extractor import ClaimExtractor
from app.extractors.evidence_extractor import EvidenceExtractor
from app.verification.candidate_matcher import CandidateMatcher
from app.verification.label_generator import LabelGenerator
from app.utils.language_detector import LanguageDetector

async def test():
    crawler = AsyncCrawler(timeout=6.0)
    engine = AsyncSearchEngine(crawler)

    # Clear search caches
    engine._search_cache.clear()

    queries = {
        "ta": "குடியரசு துணைத் தலைவர் பயணம் 2026",
        "mr": "उपराष्ट्रपती दौरा 2026",
        "hi": "उपराष्ट्रपति दौरा 2026",
        "en": "Vice President visit 2026"
    }

    for lang, q in queries.items():
        print("\n" + "=" * 70, flush=True)
        print(f"SEARCHING DIRECT ARTICLES FOR [{lang.upper()}]: '{q}'", flush=True)
        print("=" * 70, flush=True)

        ddg_res = await engine._search_duckduckgo_html(q, language=lang, max_results=8)
        bing_news = await engine._search_bing_news(q, language=lang, max_results=8)
        bing_web = await engine._search_bing_web(q, language=lang, max_results=8)
        feeds = await engine._search_direct_feeds(q, language=lang, max_results=8)

        all_res = ddg_res + bing_news + bing_web + feeds
        # Filter out news.google.com
        direct_res = [r for r in all_res if not "news.google.com" in r.get("url", "")]
        print(f"[{lang.upper()}] Total Direct Results: {len(direct_res)}", flush=True)
        for r in direct_res[:4]:
            print(f"   * Title: {r.get('title')[:60]}", flush=True)
            print(f"     URL:   {r.get('url')}", flush=True)

            # Test fetch and extract
            doc = await crawler.fetch_and_extract(r['url'], source_type="news", source_name=r.get('source', 'Web'))
            if doc and doc.get("paragraphs"):
                txt = doc.get("text", "") or " ".join(doc.get("paragraphs", []))
                print(f"     [FETCH OK] Paras: {len(doc.get('paragraphs', []))}, Text Len: {len(txt)}", flush=True)
                claims = ClaimExtractor.extract_claims_from_text(txt, title=doc.get("title", ""))
                print(f"     [CLAIMS] Extracted: {len(claims)}", flush=True)
                if claims:
                    print(f"       Sample Claim: {claims[0]['claim_text'][:80]}", flush=True)
            else:
                print("     [FETCH FAILED]", flush=True)

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(test())
