import time
import sys
from app.services.scraper_service import ScraperService, CrawlRequest

s = ScraperService()
req = CrawlRequest(query="vice president visit 2026", language="all", target_count=30)
s.start_scraping(req)
s.current_thread.join(timeout=90)

print("\n" + "="*80, flush=True)
print("SCRAPER LIVE EXECUTION LOGS:", flush=True)
print("="*80, flush=True)
for entry in s.logs:
    print(f"[{entry['timestamp']}][{entry['level']}] {entry['message']}", flush=True)

print("\n" + "="*80, flush=True)
print("FINAL FUNNEL METRICS:", flush=True)
print("="*80, flush=True)
status = s.get_status()
for k, v in status["funnel"].items():
    print(f"  {k}: {v}", flush=True)

print("\nPER-LANGUAGE COLLECTED COUNTS:", flush=True)
for lang, count in status["language_counts"].items():
    print(f"  {lang.upper()}: {count}", flush=True)

print("="*80, flush=True)
