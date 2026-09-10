import asyncio
import feedparser
import urllib.parse
import httpx

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def inspect_feed():
    query = "குடியரசு துணைத் தலைவர் பயணம் 2026"
    rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ta&gl=IN&ceid=IN:ta"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(rss_url, headers=headers)
        feed = feedparser.parse(resp.text)
        print(f"Total entries: {len(feed.entries)}")
        for i, entry in enumerate(feed.entries[:5]):
            print(f"\n--- ENTRY {i} ---")
            print("Title:", entry.get("title"))
            print("Link:", entry.get("link"))
            print("Summary HTML:", entry.get("summary"))
            # Parse links in summary
            soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
            for a in soup.find_all("a"):
                print("  Summary A href:", a.get("href"), "| text:", a.get_text())

if __name__ == "__main__":
    asyncio.run(inspect_feed())
