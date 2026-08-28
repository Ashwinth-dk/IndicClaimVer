import json
import re
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import requests
from bs4 import BeautifulSoup
from backend.config import CRAWLED_DATA_PATH, EVIDENCE_POOL_PATH, USER_AGENT
from backend.data_pipeline import normalize_text, canonical_label, load_json_records

class FactCheckCrawler:
    """
    Multi-Source Web Scraper & Crawler for Fact-Checking Portals & News Feeds.
    Collects real-world verified claims, justifications/evidence, and labels
    for continuous training dataset expansion.
    """
    def __init__(self, output_path: Path = CRAWLED_DATA_PATH):
        self.output_path = output_path
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        self.is_running = False
        self.crawled_count = 0

    def crawl_google_factcheck(self, query: str = "fact check India", max_results: int = 20) -> List[Dict[str, Any]]:
        """Alias for news & fact-checking RSS crawler."""
        return self.crawl_news_rss(query=query, max_results=max_results)

    def crawl_query(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """Crawls fact-checking items for a specific search query."""
        return self.crawl_news_rss(query=query, max_results=max_results)

    def crawl_news_rss(self, query: str = "fact check India", max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Uses Google News RSS & Fact Check Feeds (100% reliable, zero API key required).
        """
        results = []

        try:
            encoded_query = urllib.parse.quote(query + " fact check")
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            
            resp = requests.get(rss_url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find("channel")
                if channel is not None:
                    items = channel.findall("item")
                    for i, item in enumerate(items[:max_results]):
                        title_el = item.find("title")
                        link_el = item.find("link")
                        pubdate_el = item.find("pubDate")
                        desc_el = item.find("description")
                        source_el = item.find("source")

                        raw_title = title_el.text if title_el is not None else ""
                        link = link_el.text if link_el is not None else ""
                        pub_date = pubdate_el.text if pubdate_el is not None else datetime.now().strftime("%Y-%m-%d")
                        publisher = source_el.text if source_el is not None else "FactCheck Portal"
                        
                        raw_desc = ""
                        if desc_el is not None and desc_el.text:
                            soup = BeautifulSoup(desc_el.text, "html.parser")
                            raw_desc = soup.get_text()

                        claim = normalize_text(raw_title.split(" - ")[0] if " - " in raw_title else raw_title)
                        evidence = normalize_text(f"{raw_title}. {raw_desc}. Verified by {publisher}.")
                        
                        # Infer label from debunk keywords
                        label = "REFUTES" if any(w in evidence.lower() for w in ["false", "fake", "hoax", "misleading", "debunk", "myth", "incorrect", "altered"]) else "SUPPORTS"

                        if claim and len(claim) > 15 and len(evidence) > 40:
                            results.append({
                                "ID": f"CRAWL_RSS_{len(results)}_{int(time.time())}",
                                "Text": claim,
                                "Evidence": evidence,
                                "Label": label
                            })
        except Exception as e:
            print(f"News RSS crawl note: {e}")

        return results

    def crawl_politifact_rss(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Scrapes verified fact checks directly from PolitiFact RSS.
        """
        results = []
        try:
            url = "https://www.politifact.com/rss/factchecks/"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for item in items[:max_results]:
                    title_el = item.find("title")
                    link_el = item.find("link")
                    desc_el = item.find("description")
                    pub_date_el = item.find("pubDate")

                    title = title_el.text if title_el is not None else ""
                    desc = desc_el.text if desc_el is not None else ""

                    if desc:
                        soup = BeautifulSoup(desc, "html.parser")
                        text_desc = soup.get_text()
                    else:
                        text_desc = title

                    claim = normalize_text(title)
                    claim = re.sub(r"^(fact check|fact-check|fact check:|fact-check:)\s*", "", claim, flags=re.IGNORECASE).strip()
                    evidence = normalize_text(f"{text_desc} Verified and reported by PolitiFact.")
                    label = "REFUTES" if any(w in evidence.lower() for w in ["false", "pants on fire", "barely true", "misleading", "incorrect"]) else "SUPPORTS"

                    if claim and len(claim) > 15 and len(evidence) > 40:
                        results.append({
                            "ID": f"CRAWL_POLITIFACT_{len(results)}_{int(time.time())}",
                            "Text": claim,
                            "Evidence": evidence,
                            "Label": label
                        })
        except Exception as e:
            print(f"PolitiFact RSS note: {e}")
        return results

    def crawl_preset_topics(
        self,
        topics: Optional[List[str]] = None,
        max_per_topic: int = 15,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Crawls multi-domain claims (Politics, Health, COVID, Science, Elections).
        """
        if topics is None:
            topics = [
                "Narendra Modi",
                "COVID-19 vaccine health",
                "India Supreme Court",
                "Mamata Banerjee",
                "Inflation economy growth",
                "Fact Check India viral"
            ]

        self.is_running = True
        all_crawled: List[Dict[str, Any]] = []

        # 1. Fetch PolitiFact
        if progress_callback:
            progress_callback("Crawling PolitiFact RSS Feed...", 10)
        politifact_records = self.crawl_politifact_rss(max_results=max_per_topic)
        all_crawled.extend(politifact_records)

        # 2. Fetch Topics via RSS News Feeds
        for idx, topic in enumerate(topics):
            if not self.is_running:
                break
            pct = 15 + int((idx / len(topics)) * 80)
            if progress_callback:
                progress_callback(f"Crawling topic: {topic}...", pct)
            
            records = self.crawl_news_rss(topic, max_results=max_per_topic)
            all_crawled.extend(records)
            time.sleep(0.3)

        # Save to disk
        saved_count = self.save_crawled_dataset(all_crawled)
        self.is_running = False
        if progress_callback:
            progress_callback(f"Completed! Saved {saved_count} new fact-checking items.", 100)

        return all_crawled

    def save_crawled_dataset(self, new_records: List[Dict[str, Any]]) -> int:
        """
        Appends new records to crawled_dataset.json strictly with the 4 fields: ID, Text, Evidence, Label.
        """
        if not new_records:
            return 0

        existing = load_json_records(self.output_path)
        # Standardize existing records to exact 4 fields
        clean_existing = []
        for x in existing:
            c = normalize_text(x.get("Text") or x.get("claim") or "")
            ev = normalize_text(x.get("Evidence") or x.get("evidence") or "")
            lbl = canonical_label(x.get("Label") or x.get("label") or "REFUTES")
            if c and ev:
                clean_existing.append({
                    "ID": x.get("ID", f"CRAWL_{len(clean_existing)}"),
                    "Text": c,
                    "Evidence": ev,
                    "Label": lbl
                })

        existing_claims = {normalize_text(x["Text"]).lower() for x in clean_existing}
        
        added = 0
        for item in new_records:
            c = normalize_text(item.get("Text") or item.get("claim") or "")
            ev = normalize_text(item.get("Evidence") or item.get("evidence") or "")
            lbl = canonical_label(item.get("Label") or item.get("label") or "REFUTES")
            if c and ev and c.lower() not in existing_claims:
                clean_existing.append({
                    "ID": f"CRAWL/{len(clean_existing)+1:04d}",
                    "Text": c,
                    "Evidence": ev,
                    "Label": lbl
                })
                existing_claims.add(c.lower())
                added += 1

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(clean_existing, f, indent=4, ensure_ascii=False)

        self._append_to_evidence_pool(new_records)
        self.crawled_count = len(clean_existing)
        print(f"Saved {added} unique crawled records. Total crawled repository: {self.crawled_count}")
        return added

    def _append_to_evidence_pool(self, new_records: List[Dict[str, Any]]):
        """Appends crawled evidence passages to evidence_pool.json."""
        if not EVIDENCE_POOL_PATH.exists():
            return
        try:
            pool = load_json_records(EVIDENCE_POOL_PATH)
            pool_texts = {normalize_text(x.get("Evidence") or "") for x in pool}
            
            pool_added = 0
            for item in new_records:
                ev = normalize_text(item.get("Evidence") or "")
                if ev and ev not in pool_texts:
                    pool.append({
                        "ID": item.get("ID", f"EV_CRAWL_{len(pool)}"),
                        "Evidence": ev
                    })
                    pool_texts.add(ev)
                    pool_added += 1
            if pool_added > 0:
                with open(EVIDENCE_POOL_PATH, "w", encoding="utf-8") as f:
                    json.dump(pool, f, indent=4, ensure_ascii=False)
                print(f"Appended {pool_added} passages to evidence_pool.json.")
        except Exception as e:
            print(f"Error appending to evidence pool: {e}")

# Global singleton
_crawler_instance: Optional[FactCheckCrawler] = None

def get_crawler() -> FactCheckCrawler:
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = FactCheckCrawler()
    return _crawler_instance
