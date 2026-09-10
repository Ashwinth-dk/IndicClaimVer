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

async def main():
    crawler = AsyncCrawler()
    engine = AsyncSearchEngine(crawler)

    for lang in ["ta", "mr"]:
        intent = QueryIntentAnalyzer.analyze_query("vice president visit 2026", target_languages=[lang])
        print(f"\n====================== [{lang.upper()}] ======================")
        print("Queries:", intent.multilingual_queries.get(lang))
        print("Topic keywords:", intent.topic_keywords.get(lang))
        print("Action keywords:", intent.action_keywords.get(lang))

        accepted, rejected = await engine.search_by_intent(intent=intent, language=lang, max_results=10)
        print(f"Accepted: {len(accepted)}, Rejected: {len(rejected)}")
        print("\n--- REJECTIONS ---")
        for rej in rejected:
            diag = rej.get("stage1_diagnostics", {})
            print(f"Title: {rej.get('title')}")
            print(f"  Reason: {diag.get('rejection_reason')}")
            print(f"  Topic match: {diag.get('topic_match')}, Event match: {diag.get('event_match')}, Date match: {diag.get('date_match')}")

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
