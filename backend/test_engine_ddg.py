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

async def main():
    crawler = AsyncCrawler()
    engine = AsyncSearchEngine(crawler)

    res_ta = await engine._search_duckduckgo_html("குடியரசு துணைத் தலைவர் பயணம்", language="ta")
    print(f"DDG TA Results: {len(res_ta)}")
    for r in res_ta:
        print("  -", r['title'], "|", r['url'])

    res_mr = await engine._search_duckduckgo_html("उपराष्ट्रपती दौरा", language="mr")
    print(f"\nDDG MR Results: {len(res_mr)}")
    for r in res_mr:
        print("  -", r['title'], "|", r['url'])

    await crawler.close()

if __name__ == "__main__":
    asyncio.run(main())
