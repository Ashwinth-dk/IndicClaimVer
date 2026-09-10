import asyncio
import httpx
import re
import json

async def decode_google_news_token(token: str) -> str:
    url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Referer": "https://news.google.com/"
    }
    # Payload format for garturlreq
    payload = f'f.req=[[["Fbv4je","[\\"garturlreq\\",[\\"en-IN\\",\\"IN\\",[\\"FINANCE_TOP_INDICES\\",\\"WEB_TEST_1_0_0\\"],null,null,1,1,\\"IN:en\\",null,180,null,null,null,null,null,0,null,null,[1608,4383]],\\"en-IN\\",\\"IN\\",1,[2,3,4,8],1,0,\\"655000234\\",0,0,null,0],\\"{token}\\"]",null,"generic"]]]'
    
    async with httpx.AsyncClient(timeout=6.0) as client:
        try:
            resp = await client.post(url, data=payload, headers=headers)
            if resp.status_code == 200:
                lines = resp.text.split("\n")
                for line in lines:
                    if "http" in line:
                        # Extract the target URL
                        urls = re.findall(r'https?://[^\s"\\\]]+', line)
                        for u in urls:
                            if not "google.com" in u and not "gstatic.com" in u:
                                return u
        except Exception as e:
            print("Batch execute error:", e)
    return ""

async def main():
    tokens = [
        "CBMi2AFBVV95cUxOLVVacTZVRXJrZlNrdDRIVlZwanRTTTN4Vzhjbk01czNTYXpXR0d4MkxWc2dFa24tVnExd3FMT2FUd1RmRVZIZDZYNmUzTXpNdDVRNy04RGFBd3dVUVNHdnVmN29UeVNRTE5BZ2xqbDRtRWs0YTdrYlZTOEhTa3ZUU21uUjBlN0J2TzIzTjcwRGpSUTlvdUFyOTZldklMOXk5WUc1VjN2elp4S3VtdklOX0xSSk5tS1BYSGRKampiYWViSzZtSWl4UDBjQm5DRDF1X3VodzFPZHTSAdgBQVVfeXFMTi1VWnE2VUVya2ZTa3Q0SFZWcGp0U00zeFc4Y25NNXMzU2F6V0dHeDJMVnNnRWtuLVZxMXdxTE9hVHdUZkVWSGQ2WDZlM016TXQ1UTctOERhQXd3VVFTR3Z1ZjdvVHlTUUxOQWdsamw0bUVrNGE3a2JWUzhIU2t2VFNtblIwZTdCdk8yM043MERqUlE5b3VBcjk2ZXZJTDl5OVlHNVYzdnpaeEt1bXZJTl9MUkpObUtQWEhkSmpqYmFlYks2bUlpeFAwY0JuQ0QxdV91aHcxT2R0",
        "CBMioAFBVV95cUxPREZaZHJ"
    ]
    for t in tokens:
        res = await decode_google_news_token(t)
        print("Decoded URL:", res)

if __name__ == "__main__":
    asyncio.run(main())
