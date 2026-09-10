import asyncio
import unittest
from app.crawlers.topic_filter import TopicRelevanceFilter
from app.crawlers.async_search_engine import AsyncSearchEngine
from app.crawlers.async_crawler import AsyncCrawler

class TestScraperTopicIsolation(unittest.IsolatedAsyncioTestCase):

    async def test_topic_filter_on_search_engine_results(self):
        crawler = AsyncCrawler(max_concurrent_requests=5, timeout=4.0)
        search_engine = AsyncSearchEngine(crawler)

        query = "COVID-19 vaccination drive in India"
        try:
            results = await search_engine.search(query=query, max_results=6, timeout=5.0)
            print(f"\n[TEST] Retrieved {len(results)} search results for query: '{query}'")
            for i, r in enumerate(results):
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                is_rel, score, reason = TopicRelevanceFilter.is_relevant(query, title, snippet=snippet)
                print(f"  {i+1}. [{r.get('source_type')}] {title[:60]}... (Rel score: {score}, Relevant: {is_rel})")
                self.assertTrue(is_rel, f"Result '{title}' must be relevant to topic '{query}'")
        finally:
            await crawler.close()

if __name__ == "__main__":
    unittest.main()
