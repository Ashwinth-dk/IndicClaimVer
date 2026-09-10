import asyncio
from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.async_search_engine import AsyncSearchEngine

async def test_strategies():
    c = AsyncCrawler()
    se = AsyncSearchEngine(c)
    
    queries = [
        "उपराष्ट्रपती site:loksatta.com",
        "उपराष्ट्रपती site:maharashtratimes.com",
        "उपराष्ट्रपती राधाकृष्णन",
        "भारताचे उपराष्ट्रपती",
        "Vice President Maharashtra visit",
        "उपराष्ट्रपती दौरा"
    ]
    
    for q in queries:
        res = await se.search_google_news_rss(q, language="mr")
        bing_res = await se.search_bing_news(q, language="mr")
        print(f"Query '{q}': Google RSS={len(res)}, Bing={len(bing_res)}")
        for r in res[:2]:
            print(f"  [G] {r.get('title')}")
        for r in bing_res[:2]:
            print(f"  [B] {r.get('title')}")

if __name__ == "__main__":
    asyncio.run(test_strategies())
