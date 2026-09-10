import asyncio
import httpx
from bs4 import BeautifulSoup

async def test_gn():
    url = "https://news.google.com/rss/articles/CBMiuAFBVV95cUxORVU4OHR"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}, Final URL: {resp.url}, Length: {len(resp.text)}")
            soup = BeautifulSoup(resp.text, "html.parser")
            print("Title:", soup.title.string if soup.title else "No title")
            # Check for redirect links
            a_tags = soup.find_all("a")
            for a in a_tags[:5]:
                print("A href:", a.get("href"))
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test_gn())
