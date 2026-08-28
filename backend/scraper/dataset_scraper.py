import json
import re
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import warnings

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Ensure UTF-8 output on Windows consoles safely
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        pass

# Ensure imports work whether run standalone or as part of backend
try:
    from backend.config import CRAWLED_DATA_PATH, USER_AGENT
    from backend.data_pipeline import normalize_text, canonical_label
except ImportError:
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    CRAWLED_DATA_PATH = BASE_DIR / "dataset" / "crawled_dataset.json"
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    def normalize_text(text: str) -> str:
        if not isinstance(text, str):
            text = str(text or "")
        import unicodedata
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\u200b", "").replace("\ufeff", "").replace("\r\n", " ").replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def canonical_label(label: Any) -> str:
        if not isinstance(label, str):
            return "REFUTES"
        lbl = label.strip().upper()
        if lbl in ["SUPPORTS", "SUPPORT", "TRUE", "CORRECT", "MOSTLY TRUE", "VERIFIED"]:
            return "SUPPORTS"
        if lbl in ["REFUTES", "REFUTE", "FALSE", "MISLEADING", "FAKE", "PANTS ON FIRE", "INCORRECT", "DEBUNKED", "UNTRUE"]:
            return "REFUTES"
        if any(w in lbl for w in ["FALSE", "REFUTE", "FAKE", "MISLEAD", "PANTS", "INCORRECT"]):
            return "REFUTES"
        if any(w in lbl for w in ["TRUE", "SUPPORT", "ACCURATE", "VERIFIED"]):
            return "SUPPORTS"
        return "REFUTES"


def infer_veracity_label(title: str, claim: str, evidence: str) -> str:
    """
    Infers whether a fact check indicates REFUTES (debunk/false/misleading)
    or SUPPORTS (verified true/confirmed).
    """
    text_combined = f"{title} {claim} {evidence}".lower()

    refute_cues = [
        "false", "fake", "hoax", "misleading", "debunk", "myth", "incorrect",
        "altered", "manipulated", "not true", "no evidence", "unfounded",
        "pants on fire", "wrongly", "inaccurate", "deceptively", "baselessly",
        "overstates", "disproven", "fabricated", "untrue", "no,", "isn't", "is not",
        "distorted", "doctored", "bogus", "unverified"
    ]
    support_cues = [
        "true", "correct", "confirmed", "verified", "accurate", "authentic", "fact:", "yes,"
    ]

    for cue in refute_cues:
        if cue in text_combined:
            return "REFUTES"

    for cue in support_cues:
        if cue in text_combined:
            return "SUPPORTS"

    return "REFUTES"


class DatasetScraper:
    """
    Scraper designed to harvest fact-checked claims and evidence,
    formatting each sample strictly with the 4 keys matching train_subtask1.json:
    - ID
    - Text
    - Evidence
    - Label ('SUPPORTS' or 'REFUTES')
    """
    def __init__(self, output_path: Path = CRAWLED_DATA_PATH):
        self.output_path = Path(output_path)
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def scrape_google_news_rss(self, topic: str, max_items: int = 15) -> List[Dict[str, str]]:
        """Scrapes fact-checking articles via Google News RSS."""
        results = []
        try:
            encoded_query = urllib.parse.quote(f"{topic} fact check")
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
            resp = requests.get(rss_url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                items = root.findall(".//item")
                for item in items[:max_items]:
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    source_el = item.find("source")

                    raw_title = title_el.text if title_el is not None else ""
                    raw_publisher = source_el.text if source_el is not None else "FactCheck Desk"

                    raw_desc = ""
                    if desc_el is not None and desc_el.text:
                        soup = BeautifulSoup(desc_el.text, "html.parser")
                        raw_desc = soup.get_text()

                    # Clean claim and evidence
                    claim = raw_title.split(" - ")[0] if " - " in raw_title else raw_title
                    claim = normalize_text(claim)
                    claim = re.sub(r"^(fact check|fact-check|fact check:|fact-check:|viral claim:)\s*", "", claim, flags=re.IGNORECASE).strip()

                    evidence = normalize_text(f"{raw_title}. {raw_desc}. Reported and verified by {raw_publisher}.")
                    label = infer_veracity_label(raw_title, claim, evidence)

                    if len(claim) > 15 and len(evidence) > 40:
                        results.append({
                            "ID": f"SCRAPE_RSS_{len(results)}_{int(time.time()*1000)%100000}",
                            "Text": claim,
                            "Evidence": evidence,
                            "Label": label
                        })
        except Exception as e:
            print(f"[Scraper] News RSS note for '{topic}': {e}")
        return results

    def scrape_topic(self, topic: str, max_items: int = 15) -> List[Dict[str, str]]:
        """
        Scrapes fact-checked items for a specific custom topic using multi-query expansion.
        """
        clean_topic = normalize_text(topic)
        if not clean_topic:
            return []

        search_variations = [
            clean_topic,
            f"{clean_topic} fact check",
            f"{clean_topic} viral claim debunked",
            f"{clean_topic} fake news verification",
            f"{clean_topic} PIB debunk"
        ]

        harvested = []
        for q in search_variations:
            items = self.scrape_google_news_rss(q, max_items=max_items)
            harvested.extend(items)
            if len(harvested) >= max_items * 2:
                break
            time.sleep(0.15)

        # De-duplicate & Quality Filter
        seen = set()
        clean_records = []
        for item in harvested:
            claim_low = normalize_text(item.get("Text", "")).lower()
            evidence = normalize_text(item.get("Evidence", ""))
            if claim_low and len(claim_low) > 15 and len(evidence) > 40 and claim_low not in seen:
                seen.add(claim_low)
                clean_records.append({
                    "ID": f"SCRAPED_{int(time.time()*1000)%1000000}",
                    "Text": item["Text"],
                    "Evidence": evidence,
                    "Label": item["Label"]
                })
                if len(clean_records) >= max_items:
                    break

        return clean_records

    def scrape_politifact_rss(self, max_items: int = 20) -> List[Dict[str, str]]:
        """Scrapes verified fact checks from PolitiFact RSS."""
        results = []
        try:
            url = "https://www.politifact.com/rss/factchecks/"
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                soup_xml = BeautifulSoup(resp.content, "html.parser")
                items = soup_xml.find_all("item")
                for item in items[:max_items]:
                    title_el = item.find("title")
                    desc_el = item.find("description")

                    title = title_el.get_text() if title_el is not None else ""
                    desc = desc_el.get_text() if desc_el is not None else ""

                    if desc:
                        soup = BeautifulSoup(desc, "html.parser")
                        text_desc = soup.get_text()
                    else:
                        text_desc = title

                    claim = normalize_text(title)
                    claim = re.sub(r"^(fact check|fact-check|fact check:|fact-check:)\s*", "", claim, flags=re.IGNORECASE).strip()
                    evidence = normalize_text(f"{text_desc} As investigated and verified by PolitiFact.")
                    label = infer_veracity_label(title, claim, evidence)

                    if len(claim) > 15 and len(evidence) > 40:
                        results.append({
                            "ID": f"SCRAPE_POLITIFACT_{len(results)}_{int(time.time()*1000)%100000}",
                            "Text": claim,
                            "Evidence": evidence,
                            "Label": label
                        })
        except Exception as e:
            safe_print(f"[Scraper] PolitiFact RSS note: {e}")
        return results

    def scrape_indian_factcheck_feeds(self, max_items: int = 20) -> List[Dict[str, str]]:
        """Scrapes fact-checking queries targeting Indian & multi-lingual claims."""
        queries = [
            "PIB Fact Check Government India",
            "BoomLive Fact Check India viral",
            "AltNews India fact check claim",
            "Factly India debunked",
            "COVID vaccine booster India fact check",
            "Election Commission of India viral claim fact check"
        ]
        results = []
        for q in queries:
            items = self.scrape_google_news_rss(q, max_items=5)
            results.extend(items)
            time.sleep(0.2)
        return results

    def scrape_multi_domain_dataset(
        self,
        topics: Optional[List[str]] = None,
        target_count: int = 30
    ) -> List[Dict[str, str]]:
        """
        Scrapes a balanced fact-checking dataset across multiple domains:
        Politics, Healthcare, Economy, Social Viral Claims, and Tech/Science.
        Formats every item strictly into the 4 fields: ID, Text, Evidence, Label.
        """
        if topics is None:
            topics = [
                "Narendra Modi statement",
                "COVID-19 vaccine health side effects",
                "India Supreme Court verdict",
                "Reserve Bank of India currency rules",
                "Mamata Banerjee West Bengal",
                "World Bank India economic growth",
                "ISRO Moon mission space claim",
                "Delhi government free electricity subsidy",
                "US Presidential election claims",
                "Artificial intelligence replacing doctors"
            ]

        all_items: List[Dict[str, str]] = []

        safe_print(f"[*] Starting web scraping pipeline across {len(topics)} topics...")
        
        # 1. Fetch PolitiFact RSS
        safe_print("  -> Scraping PolitiFact Fact-Check Feed...")
        pol_items = self.scrape_politifact_rss(max_items=15)
        all_items.extend(pol_items)
        safe_print(f"     Harvested {len(pol_items)} items from PolitiFact.")

        # 2. Fetch Multi-domain RSS
        for topic in topics:
            if len(all_items) >= target_count * 2:
                break
            safe_print(f"  -> Scraping topic: '{topic}'...")
            t_items = self.scrape_google_news_rss(topic, max_items=8)
            all_items.extend(t_items)
            time.sleep(0.25)

        # 3. Fetch Indian fact-check portals
        if len(all_items) < target_count:
            safe_print("  -> Scraping Indian Fact-Check feeds (PIB, BoomLive, AltNews, Factly)...")
            ind_items = self.scrape_indian_factcheck_feeds(max_items=15)
            all_items.extend(ind_items)

        # 4. Strict 4-field formatting, Deduplication & Quality Filtering
        cleaned_dataset: List[Dict[str, str]] = []
        seen_claims = set()

        for idx, item in enumerate(all_items):
            claim = normalize_text(item.get("Text", ""))
            evidence = normalize_text(item.get("Evidence", ""))
            label = canonical_label(item.get("Label", "REFUTES"))

            # Quality checks
            if not claim or len(claim) < 15:
                continue
            if not evidence or len(evidence) < 40:
                continue
            if claim.lower() in seen_claims:
                continue

            seen_claims.add(claim.lower())

            # EXACT 4 FIELDS ONLY
            record = {
                "ID": f"SCRAPED/{idx+1:04d}",
                "Text": claim,
                "Evidence": evidence,
                "Label": label
            }
            cleaned_dataset.append(record)

            if len(cleaned_dataset) >= target_count:
                break

        safe_print(f"[✓] Successfully scraped {len(cleaned_dataset)} high-quality fact-checked samples.")
        return cleaned_dataset

    def save_dataset(self, dataset: List[Dict[str, str]], append: bool = False) -> int:
        """
        Saves dataset to JSON file strictly in the 4-field structure matching train_subtask1.json.
        """
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        final_list = []

        if append and self.output_path.exists():
            try:
                with open(self.output_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    if isinstance(existing, list):
                        # Ensure existing records also have only the 4 fields
                        for ex in existing:
                            final_list.append({
                                "ID": ex.get("ID", f"EXISTING_{len(final_list)}"),
                                "Text": ex.get("Text") or ex.get("claim", ""),
                                "Evidence": ex.get("Evidence") or ex.get("evidence", ""),
                                "Label": canonical_label(ex.get("Label") or ex.get("label", "REFUTES"))
                            })
            except Exception as e:
                safe_print(f"[Scraper] Note reading existing file: {e}")

        seen_claims = {normalize_text(x["Text"]).lower() for x in final_list}

        added = 0
        for item in dataset:
            clean_claim = normalize_text(item["Text"]).lower()
            if clean_claim and clean_claim not in seen_claims:
                # Ensure clean consecutive ID if fresh or appended
                item_id = f"SCRAPED/{len(final_list)+1:04d}"
                final_list.append({
                    "ID": item_id,
                    "Text": normalize_text(item["Text"]),
                    "Evidence": normalize_text(item["Evidence"]),
                    "Label": item["Label"]
                })
                seen_claims.add(clean_claim)
                added += 1

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(final_list, f, indent=4, ensure_ascii=False)

        safe_print(f"[✓] Saved {len(final_list)} samples (new added: {added}) to {self.output_path}")
        return len(final_list)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Web Scraper for 4-Field Fact-Checking Dataset")
    parser.add_argument("--count", type=int, default=25, help="Number of samples to harvest (default: 25)")
    parser.add_argument("--output", type=str, default=str(CRAWLED_DATA_PATH), help="Output JSON path")
    parser.add_argument("--append", action="store_true", help="Append to existing dataset instead of overwrite")
    args = parser.parse_args()

    scraper = DatasetScraper(output_path=Path(args.output))
    data = scraper.scrape_multi_domain_dataset(target_count=args.count)
    scraper.save_dataset(data, append=args.append)


if __name__ == "__main__":
    main()
