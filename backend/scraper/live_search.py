import urllib.parse
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from backend.config import USER_AGENT
from backend.data_pipeline import normalize_text

def search_live_web_evidence(claim: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Searches the live web, Wikipedia API, and News Feeds in real time for evidence.
    Returns ranked evidence passages with source links and publisher snippets.
    """
    claim_clean = normalize_text(claim)
    if not claim_clean:
        return []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    results: List[Dict[str, Any]] = []

    # 1. Check Wikipedia Knowledge API for core entity in claim
    # Extract likely entity (e.g. "Taj Mahal", "Narendra Modi", "ISRO")
    words = [w for w in re.findall(r"[A-Za-z0-9\u0900-\u097F\u0980-\u09FF]+", claim_clean) if len(w) > 2]
    candidate_entities = []
    
    # Try 2-word, 3-word or 1-word entities
    if len(words) >= 2:
        candidate_entities.append(" ".join(words[:2]))
    if len(words) >= 3:
        candidate_entities.append(" ".join(words[:3]))
    if words:
        candidate_entities.append(words[0])

    for ent in candidate_entities:
        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(ent)}"
            w_resp = requests.get(wiki_url, headers=headers, timeout=5)
            if w_resp.status_code == 200:
                w_data = w_resp.json()
                extract = w_data.get("extract", "")
                title = w_data.get("title", ent)
                if extract and len(extract) > 40:
                    results.append({
                        "id": f"WIKI_{len(results)}",
                        "evidence": normalize_text(f"{title}: {extract}"),
                        "score": 0.98,
                        "source": "Wikipedia Verified Knowledge",
                        "url": w_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "retrieval_mode": "wikipedia_knowledge_graph"
                    })
                    break
        except Exception as e:
            print(f"Wiki lookup note: {e}")

    # 2. Live Google News RSS Search
    try:
        encoded_query = urllib.parse.quote(claim_clean + " fact check")
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
        resp = requests.get(rss_url, headers=headers, timeout=8)
        
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            items = root.findall(".//item")
            for i, item in enumerate(items[:max_results]):
                title_el = item.find("title")
                link_el = item.find("link")
                source_el = item.find("source")
                desc_el = item.find("description")

                title = title_el.text if title_el is not None else ""
                link = link_el.text if link_el is not None else ""
                source_name = source_el.text if source_el is not None else "News Source"
                
                desc_text = ""
                if desc_el is not None and desc_el.text:
                    soup = BeautifulSoup(desc_el.text, "html.parser")
                    desc_text = soup.get_text()

                passage = normalize_text(f"{title}. {desc_text}")
                if len(passage) > 20:
                    results.append({
                        "id": f"LIVE_NEWS_{i}",
                        "evidence": passage,
                        "score": round(0.90 - (i * 0.05), 2),
                        "source": source_name,
                        "url": link,
                        "retrieval_mode": "live_news_feed"
                    })
    except Exception as e:
        print(f"Live News RSS search note: {e}")

    return results
