import asyncio
import sys
import time
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app.services.scraper_service import ScraperService, CrawlRequest

async def main():
    service = ScraperService()
    req = CrawlRequest(
        query="vice president visit 2026",
        language="all",
        target_count=20,
        max_concurrent_requests=6
    )

    print("=" * 70)
    print("STARTING LIVE MULTILINGUAL PIPELINE TEST FOR 'vice president visit 2026'")
    print("=" * 70)

    res = service.start_scraping(req)
    print(f"Service started: status={res.get('status')}, task_id={res.get('task_id')}", flush=True)

    for _ in range(60):
        status = service.get_status()
        funnel = status.get("funnel", {})
        print(f"[{status.get('current_action')}] | "
              f"Discovered: {funnel.get('discovered_count', 0)} | "
              f"Stage1 Passed: {funnel.get('potentially_relevant_stage1', 0)} | "
              f"Downloaded: {funnel.get('downloaded_count', 0)} | "
              f"Stage2 Relevant: {funnel.get('relevant_stage2', 0)} | "
              f"Verified: {funnel.get('verified_count', 0)} | "
              f"Langs: {status.get('language_counts')} | "
              f"Errors: {status.get('language_errors')}", flush=True)

        if not status.get("is_running") and funnel.get("discovered_count", 0) > 0:
            print("\nPipeline execution completed!", flush=True)
            break
        await asyncio.sleep(2.0)

    final_status = service.get_status()
    print("\n" + "=" * 70)
    print("FINAL SCRAPER PIPELINE STATUS")
    print("=" * 70)
    print("Funnel:", final_status.get("funnel"))
    print("Language Counts (Collected):", final_status.get("language_counts"))
    print("Language Rejected (Stage 1 & 2):", final_status.get("language_rejected"))
    print("Language Statuses:", final_status.get("language_statuses"))
    print("Saved Records:", final_status.get("saved_records"))
    print("Logs (Last 10):")
    for log in final_status.get("logs", [])[-10:]:
        print(f"  [{log.get('level')}] {log.get('message')}")

if __name__ == "__main__":
    asyncio.run(main())
