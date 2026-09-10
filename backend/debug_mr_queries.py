import asyncio
import httpx
import feedparser
import urllib.parse
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_mr_q(q: str):
    url = f"https://www.bing.com/news/search?q={urllib.parse.quote(q)}&format=rss"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "mr-IN,mr;q=0.9,hi;q=0.8,en-US;q=0.5"
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, headers=headers)
        feed = feedparser.parse(resp.text)
        print(f"\nQuery: '{q}' -> Entries: {len(feed.entries)}", flush=True)
        for e in feed.entries[:3]:
            # Extract real URL from apiclick url= param
            link = e.get("link", "")
            if "url=" in link:
                m = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url")
                if m:
                    link = m[0]
            print(f"  * {e.get('title')}", flush=True)
            print(f"    URL: {link}", flush=True)

async def main():
    queries = [
        "उपराष्ट्रपती राधाकृष्णन",
        "उपराष्ट्रपती दौरा",
        "उपराष्ट्रपती भेट",
        "उपराष्ट्रपतींचा दौरा",
        "उपराष्ट्रपती तामिळनाडू",
        "उपराष्ट्रपती महाराष्ट्र"
    ]
    for q in queries:
        await test_mr_q(q)

if __name__ == "__main__":
    asyncio.run(main())
