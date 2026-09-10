import asyncio
import sys
from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.async_search_engine import AsyncSearchEngine
from app.crawlers.query_intent import QueryIntentAnalyzer

async def test_mr():
    c = AsyncCrawler()
    se = AsyncSearchEngine(c)
    qi = QueryIntentAnalyzer.analyze_query('vice president visit 2026', ['mr'])
    print(f"Generated MR queries: {qi.multilingual_queries.get('mr', [])}")
    acc, rej = await se.search_by_intent(qi, 'mr', max_results=10)
    print(f"Accepted: {len(acc)}")
    print(f"Rejected: {len(rej)}")
    for r in rej[:5]:
        print(f"REJ TITLE: {r.get('title')}")
        print(f"DIAG: {r.get('stage1_diagnostics')}\n")
    for a in acc[:5]:
        print(f"ACC TITLE: {a.get('title')}")
        print(f"SCORE: {a.get('stage1_score')}\n")

if __name__ == "__main__":
    asyncio.run(test_mr())
