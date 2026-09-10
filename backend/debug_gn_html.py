import asyncio
import httpx
import re
from bs4 import BeautifulSoup

async def inspect_gn_html():
    url = "https://news.google.com/rss/articles/CBMi2AFBVV95cUxOLVVacTZVRXJrZlNrdDRIVlZwanRTTTN4Vzhjbk01czNTYXpXR0d4MkxWc2dFa24tVnExd3FMT2FUd1RmRVZIZDZYNmUzTXpNdDVRNy04RGFBd3dVUVNHdnVmN29UeVNRTE5BZ2xqbDRtRWs0YTdrYlZTOEhTa3ZUU21uUjBlN0J2TzIzTjcwRGpSUTlvdUFyOTZldklMOXk5WUc1VjN2elp4S3VtdklOX0xSSk5tS1BYSGRKampiYWViSzZtSWl4UDBjQm5DRDF1X3VodzFPZHTSAdgBQVVfeXFMTi1VWnE2VUVya2ZTa3Q0SFZWcGp0U00zeFc4Y25NNXMzU2F6V0dHeDJMVnNnRWtuLVZxMXdxTE9hVHdUZkVWSGQ2WDZlM016TXQ1UTctOERhQXd3VVFTR3Z1ZjdvVHlTUUxOQWdsamw0bUVrNGE3a2JWUzhIU2t2VFNtblIwZTdCdk8yM043MERqUlE5b3VBcjk2ZXZJTDl5OVlHNVYzdnpaeEt1bXZJTl9MUkpObUtQWEhkSmpqYmFlYks2bUlpeFAwY0JuQ0QxdV91aHcxT2R0?oc=5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=12.0) as client:
        resp = await client.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Look for target urls inside data attributes or c-wiz or links
        cwiz = soup.find("c-wiz")
        print("c-wiz exists:", cwiz is not None)
        
        # Check all links
        urls = set()
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and not "google.com" in href and href.startswith("http"):
                urls.add(href)
        print("External links found in <a> tags:", len(urls), list(urls)[:5])
        
        # Search for URLs in JS
        js_urls = set(re.findall(r'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}/[^\s"\'<>]+', resp.text))
        filtered = [u for u in js_urls if not "google" in u and not "gstatic" in u and not "w3.org" in u and not "schema.org" in u]
        print("Filtered URLs found in JS:", len(filtered), filtered[:5])

if __name__ == "__main__":
    asyncio.run(inspect_gn_html())
