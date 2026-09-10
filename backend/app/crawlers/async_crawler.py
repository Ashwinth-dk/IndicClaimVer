import asyncio
import random
import re
import time
import urllib.parse
from typing import Dict, Any, Optional, List, Set
import httpx
from bs4 import BeautifulSoup
from app.extractors.article_extractor import ArticleExtractor

class AsyncCrawler:
    """
    High-performance asynchronous crawler with connection pooling,
    per-domain rate limiting, strict timeouts, and in-memory caching.
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0"
    ]

    def __init__(
        self,
        max_concurrent_requests: int = 40,
        requests_per_domain: int = 8,
        request_delay: float = 0.0,
        timeout: float = 4.5
    ):
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        self.domain_semaphores: Dict[str, asyncio.Semaphore] = {}
        self.requests_per_domain = requests_per_domain
        self.request_delay = request_delay
        self.timeout = timeout
        
        # Connection Pool
        limits = httpx.Limits(
            max_keepalive_connections=80,
            max_connections=150,
            keepalive_expiry=30.0
        )
        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=httpx.Timeout(self.timeout, connect=2.5),
            follow_redirects=True,
            verify=False
        )

        # In-memory Caches
        self._html_cache: Dict[str, Optional[str]] = {}
        self._doc_cache: Dict[str, Optional[Dict[str, Any]]] = {}
        self._crawled_urls: Set[str] = set()
        self._lock = asyncio.Lock()

    def _get_domain_semaphore(self, domain: str) -> asyncio.Semaphore:
        if domain not in self.domain_semaphores:
            limit = 15 if "bing.com" in domain or "wikipedia.org" in domain else self.requests_per_domain
            self.domain_semaphores[domain] = asyncio.Semaphore(limit)
        return self.domain_semaphores[domain]

    async def fetch_url(self, url: str, custom_headers: Optional[Dict[str, str]] = None, language: str = "en") -> Optional[str]:
        async with self._lock:
            if url in self._html_cache:
                return self._html_cache[url]

        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or "default"
        domain_sem = self._get_domain_semaphore(domain)

        lang_header = "en-US,en;q=0.9,hi;q=0.8,ta;q=0.8,mr;q=0.8"
        if language == "ta":
            lang_header = "ta-IN,ta;q=0.9,en-US;q=0.5"
        elif language == "hi":
            lang_header = "hi-IN,hi;q=0.9,en-US;q=0.5"
        elif language == "mr":
            lang_header = "mr-IN,mr;q=0.9,en-US;q=0.5"

        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": lang_header,
            "Referer": "https://www.google.com/",
            "Connection": "keep-alive"
        }
        if custom_headers:
            headers.update(custom_headers)

        try:
            async with self.semaphore:
                async with domain_sem:
                    resp = await self.client.get(url, headers=headers)
                    if resp.status_code == 200:
                        text = resp.text
                        async with self._lock:
                            self._html_cache[url] = text
                            self._crawled_urls.add(url)
                        return text
        except Exception:
            pass

        async with self._lock:
            self._html_cache[url] = None
        return None

    async def fetch_and_extract(
        self,
        url: str,
        source_type: str = "news",
        source_name: str = "Web"
    ) -> Optional[Dict[str, Any]]:
        async with self._lock:
            if url in self._doc_cache:
                return self._doc_cache[url]

        html = await self.fetch_url(url)
        if not html:
            async with self._lock:
                self._doc_cache[url] = None
            return None

        try:
            extracted = await asyncio.to_thread(ArticleExtractor.extract_from_html, html, url)
        except Exception:
            extracted = {}

        if not extracted.get("text") and not extracted.get("paragraphs"):
            async with self._lock:
                self._doc_cache[url] = None
            return None

        doc = {
            "url": url,
            "source": source_name,
            "source_type": source_type,
            "title": extracted.get("title", ""),
            "text": extracted.get("text", ""),
            "paragraphs": extracted.get("paragraphs", []),
            "published_date": extracted.get("publish_date")
        }

        async with self._lock:
            self._doc_cache[url] = doc
        return doc

    async def fetch_urls_batch(
        self,
        items: List[Dict[str, Any]],
        timeout_per_batch: float = 6.0
    ) -> List[Dict[str, Any]]:
        tasks = []
        for it in items:
            url = it.get("url")
            if not url:
                continue
            tasks.append(self._fetch_single_item(it))
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout_per_batch
            )
        except asyncio.TimeoutError:
            results = []

        valid_docs = []
        for r in results:
            if isinstance(r, dict) and r.get("paragraphs"):
                valid_docs.append(r)
        return valid_docs

    async def _fetch_single_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            doc = await self.fetch_and_extract(
                url=item["url"],
                source_type=item.get("source_type", "news"),
                source_name=item.get("source", "Web")
            )
            if doc and item.get("published_date") and not doc.get("published_date"):
                doc["published_date"] = item["published_date"]
            return doc
        except Exception:
            return None

    def is_url_crawled(self, url: str) -> bool:
        return url in self._crawled_urls

    def get_crawled_count(self) -> int:
        return len(self._crawled_urls)

    async def close(self):
        try:
            await self.client.aclose()
        except Exception:
            pass
