import re
import hashlib
import unicodedata
from typing import List, Dict, Any, Set, Tuple, Optional
from app.utils.language_detector import LanguageDetector

class DuplicateDetector:
    """
    Detects exact duplicate claims, near-duplicate claims, and over-reused evidence
    across English, Tamil, Hindi, and Marathi.
    Preserves multi-language variations of the same factual concept as distinct training examples.
    """

    def __init__(self, existing_items: Optional[List[Dict[str, Any]]] = None):
        self.exact_hashes: Set[str] = set()
        self.token_sets: List[Tuple[str, str, Set[str]]] = []  # (item_id, lang, token_set)
        self.evidence_counts: Dict[str, int] = {}
        self.seen_urls: Set[str] = set()

        if existing_items:
            for item in existing_items:
                self.register_item(item)

    def register_item(self, item: Dict[str, Any]):
        claim = unicodedata.normalize("NFC", item.get("Text", "").strip())
        evidence = unicodedata.normalize("NFC", item.get("Evidence", "").strip())
        item_id = item.get("ID", "")
        lang = item.get("Language") or LanguageDetector.detect_language(claim)["language"]

        if claim:
            h = self._hash_text(claim, lang=lang)
            self.exact_hashes.add(h)
            tokens = self._tokenize(claim)
            self.token_sets.append((item_id, lang, tokens))

        if evidence:
            ev_h = self._hash_text(evidence)
            self.evidence_counts[ev_h] = self.evidence_counts.get(ev_h, 0) + 1

    def is_duplicate(
        self,
        claim: str,
        evidence: Optional[str] = None,
        language: Optional[str] = None,
        similarity_threshold: float = 0.82,
        max_evidence_reuse: int = 4
    ) -> Tuple[bool, str]:
        claim_clean = unicodedata.normalize("NFC", claim.strip())
        if not claim_clean:
            return True, "Empty claim text"

        detected_lang = language or LanguageDetector.detect_language(claim_clean)["language"]

        # 1. Exact hash check within same language
        h = self._hash_text(claim_clean, lang=detected_lang)
        if h in self.exact_hashes:
            return True, f"Exact duplicate claim detected in dataset ({detected_lang})"

        # 2. Near duplicate token Jaccard similarity check (within same language)
        cand_tokens = self._tokenize(claim_clean)
        if cand_tokens:
            for existing_id, ex_lang, ex_tokens in self.token_sets:
                if ex_lang == detected_lang:
                    jaccard = len(cand_tokens.intersection(ex_tokens)) / max(1, len(cand_tokens.union(ex_tokens)))
                    if jaccard >= similarity_threshold:
                        return True, f"Near duplicate claim (similarity {round(jaccard*100, 1)}% with {existing_id} in {detected_lang})"

        # 3. Evidence reuse check
        if evidence:
            ev_clean = unicodedata.normalize("NFC", evidence.strip())
            ev_h = self._hash_text(ev_clean)
            if self.evidence_counts.get(ev_h, 0) >= max_evidence_reuse:
                return True, f"Evidence text already reused {self.evidence_counts[ev_h]} times"

        return False, ""

    @staticmethod
    def _hash_text(text: str, lang: str = "") -> str:
        norm = re.sub(r'[\s\.,!?;:\"\'\(\)\[\]।॥]+', '', text.lower())
        key = f"{lang}::{norm}" if lang else norm
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    @staticmethod
    def _tokenize(text: str) -> Set[str]:
        words = re.findall(r'[\w\'-]+', text.lower(), flags=re.UNICODE)
        return {w for w in words if len(w) >= 2}
