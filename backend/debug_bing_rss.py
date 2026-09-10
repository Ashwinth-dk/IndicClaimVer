import asyncio
import httpx
import feedparser
import urllib.parse
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_bing_rss(query: str, lang: str):
    url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ta-IN,ta;q=0.9,hi-IN,hi;q=0.9,mr-IN,mr;q=0.9,en-US;q=0.5"
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, headers=headers)
        print(f"[{lang}] Bing RSS Status: {resp.status_code}", flush=True)
        feed = feedparser.parse(resp.text)
        print(f"[{lang}] Entries found: {len(feed.entries)}", flush=True)
        for i, entry in enumerate(feed.entries[:4]):
            print(f"  {i+1}. Title: {entry.get('title')}", flush=True)
            print(f"     Link:  {entry.get('link')}", flush=True)
            print(f"     Pub:   {entry.get('published')}", flush=True)

async def main():
    await test_bing_rss("Vice President visit 2026", "EN")
    await test_bing_rss("उपराष्ट्रपति दौरा 2026", "HI")
    await test_bing_rss("குடியரசு துணைத் தலைவர் பயணம்", "TA")
    await test_bing_rss("துணை ஜனாதிபதி வருகை", "TA-2")
    await test_bing_rss("उपराष्ट्रपती दौरा", "MR")
    await test_bing_rss("उपराष्ट्रपती भेट", "MR-2")

if __name__ == "__main__":
    asyncio.run(main())
