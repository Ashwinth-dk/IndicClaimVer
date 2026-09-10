import json
import os
import io
import csv
import threading
import unicodedata
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from app.utils.language_detector import LanguageDetector

class DatasetManager:
    """
    Manages the primary multilingual training dataset (train_subtask1.json).
    Ensures thread-safe atomic operations, strict validation across English,
    Tamil, Hindi, and Marathi, sequential ID generation, and metadata preservation.
    """
    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path:
            self.file_path = Path(data_file_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.file_path = base_dir / "data" / "train_subtask1.json"
        
        self.lock = threading.RLock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def load_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cleaned = []
                    for item in data:
                        text = unicodedata.normalize("NFC", str(item.get("Text", "")).strip())
                        evidence = unicodedata.normalize("NFC", str(item.get("Evidence", "")).strip())
                        label = "REFUTES" if str(item.get("Label", "")).upper() == "REFUTES" else "SUPPORTS"
                        
                        # Infer or preserve language
                        lang = item.get("Language")
                        if not lang or lang not in ["en", "ta", "hi", "mr"]:
                            lang = LanguageDetector.detect_language(text)["language"]

                        rec = {
                            "ID": str(item.get("ID", "")),
                            "Text": text,
                            "Evidence": evidence,
                            "Label": label,
                            "Language": lang
                        }
                        # Preserve optional metadata
                        if "Source" in item:
                            rec["Source"] = item["Source"]
                        if "SourceUrl" in item:
                            rec["SourceUrl"] = item["SourceUrl"]
                        if "CreatedAt" in item:
                            rec["CreatedAt"] = item["CreatedAt"]
                        if "Confidence" in item:
                            rec["Confidence"] = item["Confidence"]

                        cleaned.append(rec)
                    return cleaned
            except Exception as e:
                print(f"[DatasetManager] Error reading dataset: {e}")
                return []

    def _save_all(self, items: List[Dict[str, Any]]) -> bool:
        sanitized = []
        for it in items:
            text = unicodedata.normalize("NFC", str(it.get("Text", "")).strip())
            evidence = unicodedata.normalize("NFC", str(it.get("Evidence", "")).strip())
            label = "REFUTES" if str(it.get("Label", "")).upper() == "REFUTES" else "SUPPORTS"
            lang = it.get("Language") or LanguageDetector.detect_language(text)["language"]

            rec = {
                "ID": str(it.get("ID", "")),
                "Text": text,
                "Evidence": evidence,
                "Label": label,
                "Language": lang
            }
            if "Source" in it:
                rec["Source"] = it["Source"]
            if "SourceUrl" in it:
                rec["SourceUrl"] = it["SourceUrl"]
            if "CreatedAt" in it:
                rec["CreatedAt"] = it["CreatedAt"]
            if "Confidence" in it:
                rec["Confidence"] = it["Confidence"]

            sanitized.append(rec)

        temp_path = self.file_path.with_name(f"{self.file_path.stem}_{os.getpid()}_{threading.get_ident()}.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2, ensure_ascii=False)
            for _ in range(5):
                try:
                    if self.file_path.exists():
                        os.replace(temp_path, self.file_path)
                    else:
                        os.rename(temp_path, self.file_path)
                    return True
                except (PermissionError, OSError):
                    import time
                    time.sleep(0.05)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2, ensure_ascii=False)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return True
        except Exception as e:
            print(f"[DatasetManager] Error saving dataset: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def _get_max_id_num(self, items: List[Dict[str, Any]]) -> int:
        max_num = 0
        for item in items:
            item_id = item.get("ID", "")
            if item_id.startswith("S1/"):
                try:
                    num_part = int(item_id.split("/")[1])
                    if num_part > max_num:
                        max_num = num_part
                except (IndexError, ValueError):
                    pass
        return max_num

    def get_next_id(self) -> str:
        items = self.load_all()
        max_num = self._get_max_id_num(items)
        return f"S1/{max_num + 1:06d}"

    def add_item(
        self,
        text: str,
        evidence: str,
        label: str,
        language: Optional[str] = None,
        custom_id: Optional[str] = None,
        source: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> Dict[str, Any]:
        with self.lock:
            items = self.load_all()
            item_id = custom_id or f"S1/{self._get_max_id_num(items) + 1:06d}"
            label_clean = "REFUTES" if label.upper() == "REFUTES" else "SUPPORTS"
            clean_text = unicodedata.normalize("NFC", text.strip())
            clean_ev = unicodedata.normalize("NFC", evidence.strip())
            lang = language or LanguageDetector.detect_language(clean_text)["language"]

            new_item = {
                "ID": item_id,
                "Text": clean_text,
                "Evidence": clean_ev,
                "Label": label_clean,
                "Language": lang
            }
            if source:
                new_item["Source"] = source
            if source_url:
                new_item["SourceUrl"] = source_url

            items.append(new_item)
            self._save_all(items)
            return new_item

    def add_items_batch(self, new_items_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not new_items_data:
            return []
            
        with self.lock:
            items = self.load_all()
            added = []
            curr_id_num = self._get_max_id_num(items)

            for d in new_items_data:
                curr_id_num += 1
                item_id = f"S1/{curr_id_num:06d}"
                label_clean = "REFUTES" if str(d.get("Label", "")).upper() == "REFUTES" else "SUPPORTS"
                clean_text = unicodedata.normalize("NFC", str(d.get("Text", "")).strip())
                clean_ev = unicodedata.normalize("NFC", str(d.get("Evidence", "")).strip())
                lang = d.get("Language") or d.get("language") or LanguageDetector.detect_language(clean_text)["language"]

                item = {
                    "ID": item_id,
                    "Text": clean_text,
                    "Evidence": clean_ev,
                    "Label": label_clean,
                    "Language": lang
                }
                if "Source" in d:
                    item["Source"] = d["Source"]
                if "SourceUrl" in d:
                    item["SourceUrl"] = d["SourceUrl"]

                items.append(item)
                added.append(item)

            self._save_all(items)
            return added

    def update_item(
        self,
        item_id: str,
        text: Optional[str] = None,
        evidence: Optional[str] = None,
        label: Optional[str] = None,
        language: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self.lock:
            items = self.load_all()
            found = None
            for item in items:
                if item.get("ID") == item_id:
                    if text is not None:
                        item["Text"] = unicodedata.normalize("NFC", text.strip())
                    if evidence is not None:
                        item["Evidence"] = unicodedata.normalize("NFC", evidence.strip())
                    if label is not None:
                        item["Label"] = "REFUTES" if label.upper() == "REFUTES" else "SUPPORTS"
                    if language is not None:
                        item["Language"] = language
                    found = item
                    break

            if found:
                self._save_all(items)
            return found

    def delete_item(self, item_id: str) -> bool:
        with self.lock:
            items = self.load_all()
            initial_len = len(items)
            items = [item for item in items if item.get("ID") != item_id]
            if len(items) < initial_len:
                self._save_all(items)
                return True
            return False

    def get_stats(self) -> Dict[str, Any]:
        items = self.load_all()
        supports = sum(1 for i in items if i.get("Label") == "SUPPORTS")
        refutes = sum(1 for i in items if i.get("Label") == "REFUTES")
        total = len(items)
        ratio = round(supports / total, 3) if total > 0 else 0.0

        # Language distribution
        en_count = sum(1 for i in items if i.get("Language") == "en")
        ta_count = sum(1 for i in items if i.get("Language") == "ta")
        hi_count = sum(1 for i in items if i.get("Language") == "hi")
        mr_count = sum(1 for i in items if i.get("Language") == "mr")
        other_count = total - (en_count + ta_count + hi_count + mr_count)

        return {
            "total_count": total,
            "supports_count": supports,
            "refutes_count": refutes,
            "balance_ratio": ratio,
            "languages": {
                "en": en_count,
                "ta": ta_count,
                "hi": hi_count,
                "mr": mr_count,
                "other": other_count
            }
        }

    def query_items(
        self,
        search: Optional[str] = None,
        label: Optional[str] = None,
        language: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str = "ID",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, Any]], int]:
        items = self.load_all()

        if label and label.upper() in ["SUPPORTS", "REFUTES"]:
            items = [i for i in items if i.get("Label") == label.upper()]

        if language and language.lower() in ["en", "ta", "hi", "mr"]:
            items = [i for i in items if i.get("Language") == language.lower()]

        if search and search.strip():
            q = search.strip().lower()
            items = [
                i for i in items
                if q in i.get("Text", "").lower()
                or q in i.get("Evidence", "").lower()
                or q in i.get("ID", "").lower()
            ]

        total_filtered = len(items)
        reverse = (sort_order.lower() == "desc")
        
        if sort_by == "ID":
            items.sort(key=lambda x: x.get("ID", ""), reverse=reverse)
        elif sort_by == "Label":
            items.sort(key=lambda x: x.get("Label", ""), reverse=reverse)
        elif sort_by == "Language":
            items.sort(key=lambda x: x.get("Language", ""), reverse=reverse)

        paginated = items[offset:offset + limit]
        return paginated, total_filtered

    def export_data(self, format_type: str = "json", label_filter: Optional[str] = None, language_filter: Optional[str] = None) -> str:
        items = self.load_all()
        if label_filter and label_filter.upper() in ["SUPPORTS", "REFUTES"]:
            items = [i for i in items if i.get("Label") == label_filter.upper()]
        if language_filter and language_filter.lower() in ["en", "ta", "hi", "mr"]:
            items = [i for i in items if i.get("Language") == language_filter.lower()]

        if format_type.lower() == "json":
            return json.dumps(items, indent=2, ensure_ascii=False)
        elif format_type.lower() == "jsonl":
            return "\n".join(json.dumps(i, ensure_ascii=False) for i in items)
        elif format_type.lower() == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=["ID", "Text", "Evidence", "Label", "Language"])
            writer.writeheader()
            for item in items:
                writer.writerow({
                    "ID": item.get("ID", ""),
                    "Text": item.get("Text", ""),
                    "Evidence": item.get("Evidence", ""),
                    "Label": item.get("Label", ""),
                    "Language": item.get("Language", "en")
                })
            return output.getvalue()
        else:
            return json.dumps(items, indent=2, ensure_ascii=False)
