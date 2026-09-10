import asyncio
import httpx
import urllib.parse
from bs4 import BeautifulSoup
import sys
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_bing_web(q: str):
    url = f"https://www.bing.com/search?q={urllib.parse.quote(q)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "mr-IN,mr;q=0.9,en-US;q=0.5"
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("li", class_=re.compile(r"b_algo"))
        print(f"\nQuery: '{q}' -> Bing Web Results: {len(items)}", flush=True)
        for it in items[:4]:
            h2 = it.find("h2")
            a = h2.find("a") if h2 else None
            snip = it.find(class_=re.compile(r"b_caption|b_snippet"))
            if a:
                print(f"  * {a.get_text().strip()}", flush=True)
                print(f"    URL: {a.get('href')}", flush=True)
                print(f"    Snippet: {snip.get_text().strip()[:100] if snip else ''}", flush=True)

async def main():
    queries = [
        "उपराष्ट्रपती दौरा",
        "उपराष्ट्रपती राधाकृष्णन",
        "उपराष्ट्रपती भेट 2026",
        "उपराष्ट्रपती",
        "उपराष्ट्रपती दौरा महाराष्ट्र"
    ]
    for q in queries:
        await test_bing_web(q)

if __name__ == "__main__":
    asyncio.run(main())
