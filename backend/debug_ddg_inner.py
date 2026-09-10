import asyncio
import httpx
from bs4 import BeautifulSoup
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def main():
    query = "குடியரசு துணைத் தலைவர் பயணம்"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ta-IN,ta;q=0.9,en-US;q=0.5"
    }
    async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
        resp = await client.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query, "b": ""},
            headers=headers
        )
        print("Status:", resp.status_code, "Length:", len(resp.text))
        soup = BeautifulSoup(resp.text, "html.parser")
        results = soup.find_all("div", class_="result")
        print("Result divs:", len(results))
        for r in results[:3]:
            a = r.find("a", class_="result__a")
            print("  Title:", a.get_text() if a else "No title")
            print("  Href:", a.get("href") if a else "No href")

if __name__ == "__main__":
    asyncio.run(main())
