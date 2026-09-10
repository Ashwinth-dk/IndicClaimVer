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

from app.services.scraper_service import ScraperService, CrawlRequest

async def run_single_lang(lang: str, query: str):
    print("\n" + "=" * 70, flush=True)
    print(f"RUNNING SCRAPER FOR LANGUAGE: [{lang.upper()}] - QUERY: '{query}'", flush=True)
    print("=" * 70, flush=True)

    service = ScraperService()
    req = CrawlRequest(
        query=query,
        language=lang,
        target_count=10,
        max_concurrent_requests=6
    )

    res = service.start_scraping(req)
    print(f"Started task {res.get('task_id')}", flush=True)

    for _ in range(40):
        status = service.get_status()
        funnel = status.get("funnel", {})
        print(f"[{status.get('current_action')}] | Discovered: {funnel.get('discovered_count')} | "
              f"Stage 1: {funnel.get('potentially_relevant_stage1')} | "
              f"Downloaded: {funnel.get('downloaded_count')} | "
              f"Stage 2: {funnel.get('relevant_stage2')} | "
              f"Verified: {funnel.get('verified_count')} | Langs: {status.get('language_counts')}", flush=True)

        if not status.get("is_running") and funnel.get("discovered_count", 0) > 0:
            break
        await asyncio.sleep(2.0)

    final = service.get_status()
    print(f"\nFINAL FOR [{lang.upper()}]: Funnel={final.get('funnel')}, Collected={final.get('language_counts')}, Saved={final.get('saved_records')}", flush=True)

async def main():
    await run_single_lang("ta", "vice president visit 2026")
    await run_single_lang("mr", "vice president visit 2026")

if __name__ == "__main__":
    asyncio.run(main())
