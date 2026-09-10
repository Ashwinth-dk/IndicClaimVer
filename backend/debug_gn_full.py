import asyncio
import httpx
from bs4 import BeautifulSoup
import trafilatura

async def test_full_link():
    url = "https://news.google.com/rss/articles/CBMi2AFBVV95cUxOLVVacTZVRXJrZlNrdDRIVlZwanRTTTN4Vzhjbk01czNTYXpXR0d4MkxWc2dFa24tVnExd3FMT2FUd1RmRVZIZDZYNmUzTXpNdDVRNy04RGFBd3dVUVNHdnVmN29UeVNRTE5BZ2xqbDRtRWs0YTdrYlZTOEhTa3ZUU21uUjBlN0J2TzIzTjcwRGpSUTlvdUFyOTZldklMOXk5WUc1VjN2elp4S3VtdklOX0xSSk5tS1BYSGRKampiYWViSzZtSWl4UDBjQm5DRDF1X3VodzFPZHTSAdgBQVVfeXFMTi1VWnE2VUVya2ZTa3Q0SFZWcGp0U00zeFc4Y25NNXMzU2F6V0dHeDJMVnNnRWtuLVZxMXdxTE9hVHdUZkVWSGQ2WDZlM016TXQ1UTctOERhQXd3VVFTR3Z1ZjdvVHlTUUxOQWdsamw0bUVrNGE3a2JWUzhIU2t2VFNtblIwZTdCdk8yM043MERqUlE5b3VBcjk2ZXZJTDl5OVlHNVYzdnpaeEt1bXZJTl9MUkpObUtQWEhkSmpqYmFlYks2bUlpeFAwY0JuQ0QxdV91aHcxT2R0?oc=5"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    async with httpx.AsyncClient(follow_redirects=True, timeout=12.0) as client:
        resp = await client.get(url, headers=headers)
        print(f"Status: {resp.status_code}, Final URL: {resp.url}, Length: {len(resp.text)}")
        text = trafilatura.extract(resp.text)
        print(f"Extracted length: {len(text) if text else 0}")
        if text:
            print("Snippet:", text[:150])

if __name__ == "__main__":
    asyncio.run(test_full_link())
