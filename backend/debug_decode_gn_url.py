import base64
import re

def decode_google_news_url(source_url: str) -> str:
    match = re.search(r"articles/([^/?]+)", source_url)
    if not match:
        return source_url
    token = match.group(1)
    # Add padding
    padded = token + "=" * (-len(token) % 4)
    try:
        raw_bytes = base64.urlsafe_b64decode(padded)
        # Look for http(s) URL inside the decoded byte stream
        urls = re.findall(rb'https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}/[^\x00-\x1f\x7f-\xff"\'<> ]+', raw_bytes)
        if urls:
            return urls[0].decode("utf-8", errors="ignore")
    except Exception as e:
        print("Decode error:", e)
    return source_url

if __name__ == "__main__":
    test_urls = [
        "https://news.google.com/rss/articles/CBMi2AFBVV95cUxOLVVacTZVRXJrZlNrdDRIVlZwanRTTTN4Vzhjbk01czNTYXpXR0d4MkxWc2dFa24tVnExd3FMT2FUd1RmRVZIZDZYNmUzTXpNdDVRNy04RGFBd3dVUVNHdnVmN29UeVNRTE5BZ2xqbDRtRWs0YTdrYlZTOEhTa3ZUU21uUjBlN0J2TzIzTjcwRGpSUTlvdUFyOTZldklMOXk5WUc1VjN2elp4S3VtdklOX0xSSk5tS1BYSGRKampiYWViSzZtSWl4UDBjQm5DRDF1X3VodzFPZHTSAdgBQVVfeXFMTi1VWnE2VUVya2ZTa3Q0SFZWcGp0U00zeFc4Y25NNXMzU2F6V0dHeDJMVnNnRWtuLVZxMXdxTE9hVHdUZkVWSGQ2WDZlM016TXQ1UTctOERhQXd3VVFTR3Z1ZjdvVHlTUUxOQWdsamw0bUVrNGE3a2JWUzhIU2t2VFNtblIwZTdCdk8yM043MERqUlE5b3VBcjk2ZXZJTDl5OVlHNVYzdnpaeEt1bXZJTl9MUkpObUtQWEhkSmpqYmFlYks2bUlpeFAwY0JuQ0QxdV91aHcxT2R0?oc=5",
        "https://news.google.com/rss/articles/CBMioAFBVV95cUxPREZaZHJ"
    ]
    for u in test_urls:
        print("Decoded URL:", decode_google_news_url(u))
