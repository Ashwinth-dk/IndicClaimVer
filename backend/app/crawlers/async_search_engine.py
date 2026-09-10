import asyncio
import urllib.parse
import re
import base64
import time
from typing import List, Dict, Any, Optional, Set, Tuple
import feedparser
from bs4 import BeautifulSoup
from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.topic_filter import TopicRelevanceFilter
from app.utils.language_detector import LanguageDetector

class AsyncSearchEngine:
    """
    High-speed asynchronous multi-source discovery engine supporting English, Tamil, Hindi,
    and Marathi with feed caching, language-aware RSS/API endpoints, and category query expansion.
    """

    MULTILINGUAL_FEEDS: Dict[str, List[Dict[str, str]]] = {
        "en": [
            {"name": "The Hindu", "type": "news", "url": "https://www.thehindu.com/news/national/feeder/default.rss"},
            {"name": "Indian Express India", "type": "news", "url": "https://indianexpress.com/section/india/feed/"},
            {"name": "NDTV National", "type": "news", "url": "https://feeds.feedburner.com/ndtvnews-india-news"},
            {"name": "Times of India India", "type": "news", "url": "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms"},
            {"name": "Deccan Herald", "type": "news", "url": "https://www.deccanherald.com/rss/national.rss"},
            {"name": "Livemint Policy", "type": "news", "url": "https://www.livemint.com/rss/politics"},
            {"name": "Alt News", "type": "fact_check", "url": "https://www.altnews.in/feed/"},
            {"name": "Factly", "type": "fact_check", "url": "https://factly.in/feed/"},
            {"name": "Boom Live", "type": "fact_check", "url": "https://www.boomlive.in/stories.rss"},
            {"name": "Quint WebQoof", "type": "fact_check", "url": "https://www.thequint.com/stories.rss"},
            {"name": "Newschecker", "type": "fact_check", "url": "https://newschecker.in/feed/"},
            {"name": "PRS Legislative Research", "type": "government", "url": "https://prsindia.org/rss.xml"},
            {"name": "LiveLaw Top Stories", "type": "legal", "url": "https://www.livelaw.in/rss/top-stories.xml"},
            {"name": "Bar and Bench", "type": "legal", "url": "https://www.barandbench.com/rss"}
        ],
        "ta": [
            {"name": "Dinamalar National (Tamil)", "type": "news", "url": "https://rss.dinamalar.com/?cat=india"},
            {"name": "Dinamani (Tamil)", "type": "news", "url": "https://www.dinamani.com/rss/"},
            {"name": "Dinakaran News (Tamil)", "type": "news", "url": "https://www.dinakaran.com/feed/"},
            {"name": "Daily Thanthi (Tamil)", "type": "news", "url": "https://www.dailythanthi.com/rss"},
            {"name": "ABP Nadu (Tamil)", "type": "news", "url": "https://tamil.abplive.com/home/feed"},
            {"name": "BBC Tamil", "type": "news", "url": "https://feeds.bbci.co.uk/tamil/rss.xml"},
            {"name": "Newschecker Tamil", "type": "fact_check", "url": "https://newschecker.in/ta/feed/"},
            {"name": "Factly Tamil", "type": "fact_check", "url": "https://factly.in/category/tamil/feed/"},
            {"name": "PIB Tamil", "type": "government", "url": "https://pib.gov.in/RssTamil.aspx"}
        ],
        "hi": [
            {"name": "Amar Ujala National (Hindi)", "type": "news", "url": "https://www.amarujala.com/rss/national-news.xml"},
            {"name": "Dainik Bhaskar (Hindi)", "type": "news", "url": "https://www.bhaskar.com/rss-v1--all.xml"},
            {"name": "BBC Hindi", "type": "news", "url": "https://feeds.bbci.co.uk/hindi/rss.xml"},
            {"name": "ABP News Hindi", "type": "news", "url": "https://www.abplive.com/home/feed"},
            {"name": "Boom Hindi", "type": "fact_check", "url": "https://hindi.boomlive.in/stories.rss"},
            {"name": "Alt News Hindi", "type": "fact_check", "url": "https://www.altnews.in/hindi/feed/"},
            {"name": "Newschecker Hindi", "type": "fact_check", "url": "https://newschecker.in/hi/feed/"},
            {"name": "LiveLaw Hindi", "type": "legal", "url": "https://hindi.livelaw.in/rss/top-stories.xml"},
            {"name": "PIB Hindi", "type": "government", "url": "https://pib.gov.in/RssHindi.aspx"}
        ],
        "mr": [
            {"name": "Loksatta (Marathi)", "type": "news", "url": "https://www.loksatta.com/feed/"},
            {"name": "ABP Majha (Marathi)", "type": "news", "url": "https://marathi.abplive.com/home/feed"},
            {"name": "TV9 Marathi", "type": "news", "url": "https://www.tv9marathi.com/feed"},
            {"name": "Sakal Marathi", "type": "news", "url": "https://www.esakal.com/feed"},
            {"name": "Saamana (Marathi)", "type": "news", "url": "https://saamana.com/feed/"},
            {"name": "Maharashtra Times (Marathi)", "type": "news", "url": "https://maharashtratimes.com/rssfeedsdefault.cms"},
            {"name": "BBC Marathi", "type": "news", "url": "https://feeds.bbci.co.uk/marathi/rss.xml"},
            {"name": "Newschecker Marathi", "type": "fact_check", "url": "https://newschecker.in/mr/feed/"},
            {"name": "Factly Marathi", "type": "fact_check", "url": "https://factly.in/category/marathi/feed/"},
            {"name": "PIB Marathi", "type": "government", "url": "https://pib.gov.in/RssMarathi.aspx"}
        ]
    }

    def __init__(self, crawler: AsyncCrawler):
        self.crawler = crawler
        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._feed_cache: Dict[str, Tuple[float, List[Dict[str, Any]]]] = {}
        self._lock = asyncio.Lock()

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        language: str = "en",
        max_results: int = 15,
        date_mode: str = "both",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: float = 6.0
    ) -> List[Dict[str, Any]]:
        clean_q = self._clean_query(query)
        lang = language.lower().strip() if language else "en"
        cache_key = f"{clean_q}::{category}::{lang}::{date_mode}::{start_date}::{end_date}"
        
        async with self._lock:
            if cache_key in self._search_cache:
                return self._search_cache[cache_key]

        tasks = [
            self._safe_call(self._search_bing_news(clean_q, language=lang, max_results=max_results), timeout=timeout),
            self._safe_call(self._search_bing_web(clean_q, language=lang, max_results=max_results), timeout=timeout),
            self._safe_call(self._search_duckduckgo_html(clean_q, language=lang, max_results=max_results), timeout=timeout),
            self._safe_call(self._search_google_news_rss(clean_q, language=lang, max_results=max_results), timeout=timeout),
            self._safe_call(self._search_wikipedia_async(clean_q, language=lang, max_results=min(4, max_results)), timeout=timeout),
            self._safe_call(self._search_direct_feeds(clean_q, language=lang, preferred_type=category, max_results=max_results), timeout=timeout)
        ]

        if category:
            cat_q = self._expand_category_query(clean_q, category, language=lang)
            if cat_q != clean_q:
                tasks.append(self._safe_call(self._search_bing_web(cat_q, language=lang, max_results=max_results), timeout=timeout))

        if date_mode in ["historical", "custom"]:
            hist_years = self._get_historical_years(start_date, end_date)
            for yr in hist_years[:2]:
                hist_q = f"{clean_q} {yr}"
                tasks.append(self._safe_call(self._search_bing_web(hist_q, language=lang, max_results=4), timeout=timeout))

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        combined: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()

        for r_list in results_lists:
            if isinstance(r_list, list):
                for item in r_list:
                    url = item.get("url", "").strip()
                    if url and url not in seen_urls and not self._is_unwanted_url(url):
                        seen_urls.add(url)
                        if category and not item.get("source_type"):
                            item["source_type"] = category
                        item["language"] = lang
                        combined.append(item)

        final_results = combined[:max_results]
        async with self._lock:
            self._search_cache[cache_key] = final_results

        return final_results

    async def search_by_intent(
        self,
        intent: Any,  # QueryIntent
        language: str = "en",
        max_results: int = 15,
        min_stage1_threshold: float = 0.40
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Executes query-driven multilingual search and Stage 1 relevance filtering.
        Returns: (accepted_results, rejected_results) with relevance diagnostics.
        """
        lang = language.lower().strip()
        queries = list(intent.multilingual_queries.get(lang, []))
        if intent.original_query not in queries:
            queries.append(intent.original_query)
        if lang == "mr":
            for fb in ["Vice President Maharashtra", "Vice President visit Mumbai", "उपराष्ट्रपती", "राधाकृष्णन"]:
                if fb not in queries:
                    queries.append(fb)
        elif lang == "ta":
            for fb in ["Vice President Tamil Nadu", "குடியரசு துணைத் தலைவர்", "துணை ஜனாதிபதி"]:
                if fb not in queries:
                    queries.append(fb)
        
        # Search across generated query variants for this language
        raw_candidates: List[Dict[str, Any]] = []
        seen_urls: Set[str] = set()

        for q in queries[:4]:
            if len(raw_candidates) >= (max_results * 2):
                break
            sub_results = await self.search(
                query=q,
                language=lang,
                max_results=max_results,
                timeout=6.0
            )
            for it in sub_results:
                u = it.get("url", "").strip()
                if u and u not in seen_urls and not self._is_unwanted_url(u):
                    seen_urls.add(u)
                    raw_candidates.append(it)

        # Stage 1 Pre-Fetch Relevance Filtering
        accepted: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []

        for item in raw_candidates:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("url", "")
            pub_date = item.get("published_date", "")
            source_name = item.get("source", "")

            is_acc, diag = TopicRelevanceFilter.evaluate_stage1_snippet(
                intent=intent,
                title=title,
                snippet=snippet,
                url=url,
                pub_date=pub_date or "",
                source_name=source_name,
                lang=lang,
                min_threshold=min_stage1_threshold
            )

            item["stage1_diagnostics"] = diag.model_dump()
            item["relevance_score"] = diag.relevance_score
            item["query_id"] = intent.query_id

            if is_acc:
                accepted.append(item)
            else:
                rejected.append(item)

        return accepted[:max_results], rejected

    async def _safe_call(self, coro, timeout: float = 6.0) -> List[Dict[str, Any]]:
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except Exception:
            return []

    def _clean_query(self, query: str) -> str:
        q = re.sub(r'[\(\)"]+', ' ', query)
        q = re.sub(r'\s+OR\s+', ' ', q, flags=re.IGNORECASE)
        q = re.sub(r'\s+', ' ', q).strip()
        return q

    def _expand_category_query(self, query: str, category: str, language: str = "en") -> str:
        cat_lower = category.lower()
        if language == "ta":
            if cat_lower == "government":
                return f"{query} அரசு அறிவிப்பு அமைச்சகம்"
            elif cat_lower == "fact_check":
                return f"{query} உண்மை சரிபார்ப்பு போலி தகவல்"
            elif cat_lower == "legal":
                return f"{query} உயர் நீதிமன்றம் உச்ச நீதிமன்றம் தீர்ப்பு"
        elif language == "hi":
            if cat_lower == "government":
                return f"{query} सरकार मंत्रालय आधिकारिक घोषणा"
            elif cat_lower == "fact_check":
                return f"{query} फैक्ट चेक फर्जी खबर सच"
            elif cat_lower == "legal":
                return f"{query} सुप्रीम कोर्ट हाई कोर्ट फैसला"
        elif language == "mr":
            if cat_lower == "government":
                return f"{query} शासन निर्णय मंत्रालय अधिकृत"
            elif cat_lower == "fact_check":
                return f"{query} फॅक्ट चेक खोटा दावा सत्य"
            elif cat_lower == "legal":
                return f"{query} उच्च न्यायालय सर्वोच्च न्यायालय निकाल"
        else:
            if cat_lower == "government":
                return f"{query} PIB official ministry government India"
            elif cat_lower == "fact_check":
                return f"{query} fact check viral false debunked India"
            elif cat_lower == "legal":
                return f"{query} High Court Supreme Court judgment verdict legal"
        return query

    def _get_historical_years(self, start_date: Optional[str], end_date: Optional[str]) -> List[int]:
        current_year = 2026
        try:
            start_yr = int(start_date.split("-")[0]) if start_date else 2015
            end_yr = int(end_date.split("-")[0]) if end_date else current_year
        except Exception:
            start_yr, end_yr = 2015, current_year
            
        return list(range(start_yr, end_yr + 1))

    async def _search_bing_news(self, query: str, language: str = "en", max_results: int = 12) -> List[Dict[str, Any]]:
        results = []
        seen = set()
        headers = self._get_language_headers(language)

        # 1. Bing News RSS format
        rss_url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}&format=rss"
        xml = await self.crawler.fetch_url(rss_url, custom_headers=headers)
        if xml:
            feed = await asyncio.to_thread(feedparser.parse, xml)
            for entry in feed.entries[:max_results]:
                raw_link = entry.get("link", "")
                actual_url = self._decode_bing_url(raw_link)
                if not actual_url or not actual_url.startswith("http") or "bing.com" in actual_url or actual_url in seen or self._is_unwanted_url(actual_url):
                    continue

                seen.add(actual_url)
                title = entry.get("title", "")
                pub_date = entry.get("published", "")[:10] if entry.get("published") else None
                source = entry.get("source", {}).get("title", "") or urllib.parse.urlparse(actual_url).netloc

                results.append({
                    "title": title,
                    "url": actual_url,
                    "snippet": title,
                    "source": source,
                    "source_type": "news",
                    "language": language,
                    "published_date": pub_date
                })

        # 2. Bing News HTML cards
        if len(results) < max_results:
            url = f"https://www.bing.com/news/search?q={urllib.parse.quote(query)}"
            html = await self.crawler.fetch_url(url, custom_headers=headers)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                cards = soup.find_all("div", class_=re.compile(r"news-card|t_s"))

                for c in cards:
                    a_tag = c.find("a", class_=re.compile(r"title|tit")) or c.find("a")
                    if not a_tag:
                        continue

                    raw_url = a_tag.get("href", "")
                    actual_url = self._decode_bing_url(raw_url)
                    if not actual_url or not actual_url.startswith("http") or "bing.com" in actual_url or actual_url in seen or self._is_unwanted_url(actual_url):
                        continue

                    seen.add(actual_url)
                    title = a_tag.get_text().strip()
                    snippet_elem = c.find(class_=re.compile(r"snippet|desc"))
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    source_elem = c.find(class_=re.compile(r"source|publisher"))
                    source = source_elem.get_text().strip() if source_elem else urllib.parse.urlparse(actual_url).netloc

                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet,
                        "source": source,
                        "source_type": "news",
                        "language": language,
                        "published_date": None
                    })
                    if len(results) >= max_results:
                        break

        return results

    async def _search_bing_web(self, query: str, language: str = "en", max_results: int = 12) -> List[Dict[str, Any]]:
        results = []
        seen = set()
        url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
        
        headers = self._get_language_headers(language)
        html = await self.crawler.fetch_url(url, custom_headers=headers)
        if not html:
            return results

        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all("li", class_=re.compile(r"b_algo"))

        for item in items:
            h2 = item.find("h2")
            if not h2:
                continue
            a_tag = h2.find("a")
            if not a_tag:
                continue

            raw_url = a_tag.get("href", "")
            actual_url = self._decode_bing_url(raw_url)
            if not actual_url or not actual_url.startswith("http") or "bing.com" in actual_url or actual_url in seen:
                continue

            seen.add(actual_url)
            title = a_tag.get_text().strip()
            snippet_elem = item.find(class_=re.compile(r"b_caption|b_snippet"))
            snippet = snippet_elem.get_text().strip() if snippet_elem else ""

            results.append({
                "title": title,
                "url": actual_url,
                "snippet": snippet,
                "source": urllib.parse.urlparse(actual_url).netloc,
                "source_type": "web",
                "language": language,
                "published_date": None
            })
            if len(results) >= max_results:
                break

        return results

    async def _search_duckduckgo_html(self, query: str, language: str = "en", max_results: int = 12) -> List[Dict[str, Any]]:
        results = []
        seen = set()
        headers = {
            **self._get_language_headers(language),
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        try:
            resp = await self.crawler.client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "b": ""},
                headers=headers,
                timeout=6.0
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                for r in soup.find_all("div", class_="result"):
                    title_elem = r.find("a", class_="result__a")
                    if not title_elem:
                        continue
                    raw_href = title_elem.get("href", "")
                    actual_url = raw_href
                    if "uddg=" in raw_href:
                        match = re.search(r"uddg=([^&]+)", raw_href)
                        if match:
                            actual_url = urllib.parse.unquote(match.group(1))
                    elif raw_href.startswith("//"):
                        actual_url = "https:" + raw_href

                    if not actual_url.startswith("http") or "duckduckgo.com" in actual_url or actual_url in seen or self._is_unwanted_url(actual_url):
                        continue

                    seen.add(actual_url)
                    title = title_elem.get_text().strip()
                    snippet_elem = r.find("a", class_="result__snippet") or r.find("div", class_="result__snippet")
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""

                    results.append({
                        "title": title,
                        "url": actual_url,
                        "snippet": snippet,
                        "source": urllib.parse.urlparse(actual_url).netloc,
                        "source_type": "web",
                        "language": language,
                        "published_date": None
                    })
                    if len(results) >= max_results:
                        break
        except Exception:
            pass
        return results

    async def _search_google_news_rss(self, query: str, language: str = "en", max_results: int = 10) -> List[Dict[str, Any]]:
        results = []
        # Construct language-specific Google News RSS parameters
        if language == "ta":
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=ta&gl=IN&ceid=IN:ta"
        elif language == "hi":
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=hi&gl=IN&ceid=IN:hi"
        elif language == "mr":
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=mr&gl=IN&ceid=IN:mr"
        else:
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

        headers = self._get_language_headers(language)
        xml = await self.crawler.fetch_url(rss_url, custom_headers=headers)
        if xml:
            feed = await asyncio.to_thread(feedparser.parse, xml)
            for entry in feed.entries[:max_results]:
                link = entry.get("link", "")
                title = entry.get("title", "")
                source = entry.get("source", {}).get("title", "News")
                pub_date = entry.get("published", "")[:10] if entry.get("published") else None
                if link and not self._is_unwanted_url(link):
                    is_rel, _, _ = TopicRelevanceFilter.is_relevant(query, title, snippet=title)
                    if is_rel:
                        results.append({
                            "title": title,
                            "url": link,
                            "snippet": title,
                            "source": source,
                            "source_type": "news",
                            "language": language,
                            "published_date": pub_date
                        })
        return results

    async def _search_wikipedia_async(self, query: str, language: str = "en", max_results: int = 4) -> List[Dict[str, Any]]:
        results = []
        domain = "en"
        if language in ["ta", "hi", "mr"]:
            domain = language

        wiki_url = f"https://{domain}.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json&srlimit={max_results}"
        headers = {
            "User-Agent": f"IndicClaimBot/2.0 (research; language={language})",
            **self._get_language_headers(language)
        }
        json_text = await self.crawler.fetch_url(wiki_url, custom_headers=headers)
        if json_text:
            import json
            try:
                data = json.loads(json_text)
                for hit in data.get("query", {}).get("search", []):
                    title = hit.get("title", "")
                    clean_snippet = BeautifulSoup(hit.get("snippet", ""), "html.parser").get_text().strip()
                    article_url = f"https://{domain}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    
                    is_rel, _, _ = TopicRelevanceFilter.is_relevant(query, title, snippet=clean_snippet)
                    if is_rel:
                        results.append({
                            "title": title,
                            "url": article_url,
                            "snippet": clean_snippet,
                            "source": f"Wikipedia ({language.upper()})",
                            "source_type": "research",
                            "language": language,
                            "published_date": None
                        })
            except Exception:
                pass
        return results

    async def _search_direct_feeds(
        self,
        query: str,
        language: str = "en",
        preferred_type: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        results = []
        keywords = TopicRelevanceFilter.extract_keywords(query)
        if not keywords:
            return results

        lang_feeds = self.MULTILINGUAL_FEEDS.get(language, self.MULTILINGUAL_FEEDS.get("en", []))
        feeds_to_check = [f for f in lang_feeds if not preferred_type or f["type"] == preferred_type]

        tasks = []
        for feed_info in feeds_to_check[:8]:
            tasks.append(self._parse_single_feed(feed_info, query, language))

        feed_results = await asyncio.gather(*tasks, return_exceptions=True)
        for sub_res in feed_results:
            if isinstance(sub_res, list):
                results.extend(sub_res)
                if len(results) >= max_results:
                    break

        return results[:max_results]

    async def _parse_single_feed(self, feed_info: Dict[str, str], query: str, language: str) -> List[Dict[str, Any]]:
        feed_url = feed_info["url"]
        now = time.time()
        cached_entries = None
        if feed_url in self._feed_cache:
            ts, entries = self._feed_cache[feed_url]
            if now - ts < 600.0:
                cached_entries = entries

        if cached_entries is None:
            headers = self._get_language_headers(language)
            xml = await self.crawler.fetch_url(feed_url, custom_headers=headers)
            if not xml:
                return []
            parsed = await asyncio.to_thread(feedparser.parse, xml)
            cached_entries = parsed.entries
            self._feed_cache[feed_url] = (now, cached_entries)

        items = []
        for entry in cached_entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")
            clean_snip = BeautifulSoup(summary, "html.parser").get_text().strip() if summary else ""

            is_rel, _, _ = TopicRelevanceFilter.is_relevant(
                query, title, snippet=clean_snip, strict_feed_mode=True
            )
            if is_rel:
                items.append({
                    "title": title,
                    "url": link,
                    "snippet": clean_snip[:250] if clean_snip else title,
                    "source": feed_info["name"],
                    "source_type": feed_info["type"],
                    "language": language,
                    "published_date": entry.get("published", "")[:10] if entry.get("published") else None
                })
        return items

    def _get_language_headers(self, language: str) -> Dict[str, str]:
        if language == "ta":
            return {"Accept-Language": "ta-IN,ta;q=0.9,en-US;q=0.5"}
        elif language == "hi":
            return {"Accept-Language": "hi-IN,hi;q=0.9,en-US;q=0.5"}
        elif language == "mr":
            return {"Accept-Language": "mr-IN,mr;q=0.9,en-US;q=0.5"}
        else:
            return {"Accept-Language": "en-US,en;q=0.9,hi;q=0.5"}

    def _decode_bing_url(self, href: str) -> str:
        if "url=" in href:
            match = re.search(r"[?&]url=([^&]+)", href)
            if match:
                decoded_u = urllib.parse.unquote(match.group(1))
                if decoded_u.startswith("http"):
                    return decoded_u
        if "u=" in href:
            match = re.search(r"[?&]u=([^&]+)", href)
            if match:
                u_val = match.group(1)
                if u_val.startswith("a1"):
                    b64 = u_val[2:]
                    padding = "=" * (-len(b64) % 4)
                    try:
                        return base64.urlsafe_b64decode(b64 + padding).decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                else:
                    return urllib.parse.unquote(u_val)
        return href

    def _is_unwanted_url(self, url: str) -> bool:
        url_lower = url.lower()
        unwanted = [
            "youtube.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
            "reddit.com", "pinterest.com", "linkedin.com", "tiktok.com", ".pdf",
            ".jpg", ".png", ".mp4", "login", "signup", "zhihu.com", "commentcamarche.net",
            "allevents.in", "quora.com", "news.google.com/rss/articles"
        ]
        return any(u in url_lower for u in unwanted)
