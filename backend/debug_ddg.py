import asyncio
import httpx
import urllib.parse
from bs4 import BeautifulSoup
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def test_ddg(query: str, lang: str):
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ta,hi,mr,en-US,en;q=0.9"
    }
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        resp = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "b": ""},
            headers=headers
        )
        print(f"[{lang}] Status: {resp.status_code}")
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for r in soup.find_all("div", class_="result"):
            a = r.find("a", class_="result__url") or r.find("a", class_="result__snippet") or r.find("a")
            snippet_elem = r.find("a", class_="result__snippet") or r.find("div", class_="result__snippet")
            title_elem = r.find("a", class_="result__a")
            if title_elem and title_elem.get("href"):
                raw_href = title_elem.get("href")
                # Parse uddg= target url if present
                actual_url = raw_href
                if "uddg=" in raw_href:
                    match = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query).get("uddg")
                    if match:
                        actual_url = match[0]
                results.append({
                    "title": title_elem.get_text().strip(),
                    "url": actual_url,
                    "snippet": snippet_elem.get_text().strip() if snippet_elem else ""
                })
        print(f"[{lang}] Found {len(results)} DDG results:")
        for res in results[:3]:
            print(f"   - {res['title'][:60]} | {res['url'][:70]}")

async def main():
    await test_ddg("குடியரசு துணைத் தலைவர் பயணம் 2026", "TA")
    await test_ddg("उपराष्ट्रपती दौरा 2026", "MR")
    await test_ddg("उपराष्ट्रपति दौरा 2026", "HI")
    await test_ddg("Vice President visit 2026", "EN")

if __name__ == "__main__":
    asyncio.run(main())
