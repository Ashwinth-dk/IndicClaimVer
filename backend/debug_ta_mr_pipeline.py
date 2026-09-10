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

async def test_lang(lang: str, topic_query: str):
    print("\n" + "=" * 70)
    print(f"DEBUGGING PIPELINE FOR [{lang.upper()}] - QUERY: '{topic_query}'")
    print("=" * 70)

    intent = QueryIntentAnalyzer.analyze_query(topic_query, target_languages=[lang])
    print(f"Generated queries for [{lang}]:", intent.multilingual_queries.get(lang))

    crawler = AsyncCrawler(timeout=6.0)
    engine = AsyncSearchEngine(crawler)

    accepted, rejected = await engine.search_by_intent(intent=intent, language=lang, max_results=10)
    print(f"Stage 1 Accepted: {len(accepted)}, Rejected: {len(rejected)}")

    for i, item in enumerate(accepted):
        print(f"\n--- Candidate {i+1} [{lang.upper()}] ---")
        print(f"Title: {item.get('title')}")
        print(f"URL: {item.get('url')}")
        print(f"Relevance Score: {item.get('relevance_score')}")

        doc = await crawler.fetch_and_extract(url=item['url'], source_type=item.get('source_type', 'news'))
        if not doc or not doc.get("paragraphs"):
            print("  [FETCH FAILED] No paragraphs extracted")
            continue

        full_text = doc.get("text", "") or " ".join(doc.get("paragraphs", []))
        det_lang = LanguageDetector.detect_language(f"{doc.get('title', '')} {full_text[:500]}")["language"]
        print(f"  [FETCH SUCCESS] Paras: {len(doc.get('paragraphs', []))}, Text len: {len(full_text)}, Detected Lang: {det_lang}")

        is_rel, diag = TopicRelevanceFilter.evaluate_stage2_content(
            intent=intent,
            title=doc.get("title", ""),
            full_text=full_text,
            pub_date=doc.get("published_date", ""),
            url=item['url'],
            lang=det_lang,
            min_threshold=0.35
        )
        print(f"  [STAGE 2] Relevant: {is_rel}, Score: {diag.relevance_score:.2f}, Reasons: {diag.reasons}, Rejection: {diag.rejection_reason}")

        if is_rel:
            claims = ClaimExtractor.extract_claims_from_text(full_text, title=doc.get("title", ""))
            print(f"  [CLAIMS EXTRACTED] Count: {len(claims)}")
            for c in claims[:3]:
                print(f"    - Claim: {c['claim_text']}")
                evs = EvidenceExtractor.extract_evidence_candidates(doc.get("paragraphs", []), c['claim_text'])
                print(f"      Evidences found: {len(evs)}")
                if evs:
                    score = CandidateMatcher.compute_match_score(c['claim_text'], evs[0]['evidence_text'])
                    label, conf, _ = LabelGenerator.generate_label(c['claim_text'], evs[0]['evidence_text'], score.get('score', 0.5))
                    print(f"      Match Score: {score.get('score'):.2f}, Label: {label}, Conf: {conf:.2f}")

    await crawler.close()

async def main():
    await test_lang("ta", "vice president visit 2026")
    await test_lang("mr", "vice president visit 2026")

if __name__ == "__main__":
    asyncio.run(main())
