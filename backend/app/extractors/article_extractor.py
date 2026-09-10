import re
from typing import Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import trafilatura

class ArticleExtractor:
    """
    Cleans raw HTML or text and extracts core title, publish date,
    author, clean text body, and paragraphs.
    """

    @staticmethod
    def extract_from_html(html_content: str, url: Optional[str] = None) -> Dict[str, Any]:
        if not html_content or not html_content.strip():
            return {
                "title": "",
                "text": "",
                "paragraphs": [],
                "publish_date": None,
                "author": None
            }

        # Try trafilatura first for high-quality main text extraction
        extracted_text = trafilatura.extract(
            html_content,
            include_comments=False,
            include_tables=False,
            no_fallback=False
        )

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract title
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text().strip()

        # Clean title of common site suffixes like " | The Hindu", " - Indian Express", etc.
        title = re.sub(r"\s*[-|–—:]\s*(The Hindu|Indian Express|NDTV|Times of India|Livemint|PIB|Boomlive|Alt News|Quint|India Today|Bar and Bench|Live Law|Wikipedia).*$", "", title, flags=re.IGNORECASE)

        # Extract publish date
        publish_date = ArticleExtractor._extract_date(soup)

        # Extract text body if trafilatura had no output
        if not extracted_text:
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "button", "iframe"]):
                tag.decompose()
            
            p_tags = soup.find_all("p")
            paras = [p.get_text().strip() for p in p_tags if len(p.get_text().strip()) > 30]
            extracted_text = "\n\n".join(paras)

        clean_body = ArticleExtractor.clean_text(extracted_text or "")
        paragraphs = [
            p.strip() for p in clean_body.split("\n") 
            if len(p.strip()) >= 30 and not ArticleExtractor._is_boilerplate(p.strip())
        ]

        return {
            "title": title.strip(),
            "text": clean_body,
            "paragraphs": paragraphs,
            "publish_date": publish_date,
            "author": None
        }

    @staticmethod
    def _extract_date(soup: BeautifulSoup) -> Optional[str]:
        # Check meta tags
        date_meta_names = [
            "article:published_time", "publication_date", "date", "DC.date.issued",
            "sailthru.date", "parsely-pub-date", "pubdate", "og:pubdate"
        ]
        for name in date_meta_names:
            meta = soup.find("meta", {"property": name}) or soup.find("meta", {"name": name})
            if meta and meta.get("content"):
                date_str = meta["content"][:10]
                if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
                    return date_str

        # Check time tag
        time_tag = soup.find("time")
        if time_tag:
            if time_tag.get("datetime"):
                dt_str = time_tag["datetime"][:10]
                if re.match(r"^\d{4}-\d{2}-\d{2}$", dt_str):
                    return dt_str
            text_date = time_tag.get_text().strip()
            parsed = ArticleExtractor._parse_date_text(text_date)
            if parsed:
                return parsed

        return None

    @staticmethod
    def _parse_date_text(text: str) -> Optional[str]:
        match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", text)
        if match:
            y, m, d = match.groups()
            return f"{y}-{int(m):02d}-{int(d):02d}"
        
        # Match '12 March 2024' or 'March 12, 2024'
        match2 = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", text)
        if match2:
            d, mon, y = match2.groups()
            try:
                dt = datetime.strptime(f"{d} {mon[:3]} {y}", "%d %b %Y")
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass
        return None

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        # Remove repeated whitespace and normalize newlines
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Remove cookie / newsletter boilerplate phrases
        boilerplate_patterns = [
            r"Subscribe to our newsletter.*",
            r"Click here to read more.*",
            r"Follow us on (Twitter|Facebook|Instagram|Telegram|WhatsApp).*",
            r"All rights reserved.*",
            r"Terms of Use\s*\|\s*Privacy Policy.*",
            r"Advertisement\b",
            r"Also Read:.*",
            r"Read also:.*",
            r"Download the app now.*"
        ]
        for pat in boilerplate_patterns:
            text = re.sub(pat, "", text, flags=re.IGNORECASE)
        return text.strip()

    @staticmethod
    def _is_boilerplate(paragraph: str) -> bool:
        p_lower = paragraph.lower()
        if len(paragraph) < 25:
            return True
        signals = [
            "cookie policy", "privacy policy", "terms and conditions", "sign in to continue",
            "subscribe now", "all rights reserved", "whatsapp channel", "telegram channel",
            "share this story", "advertisement", "copyright ©"
        ]
        return any(s in p_lower for s in signals)
