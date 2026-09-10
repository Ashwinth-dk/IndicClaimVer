import json
import os
import io
import csv
import threading
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

class EvidenceManager:
    """
    Manages the independent evidence pool (evidence_pool.json).
    Ensures strict 2-field schema:
    [{"ID": "EV/100000", "Evidence": "clean extracted evidence text"}]
    Sequential ID generation (EV/100000+), deduplication by evidence text,
    and fast buffered atomic persistence.
    """
    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path:
            self.file_path = Path(data_file_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.file_path = base_dir / "data" / "evidence_pool.json"
        
        self.lock = threading.RLock()
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def load_all(self) -> List[Dict[str, str]]:
        with self.lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    cleaned = []
                    for item in data:
                        # Normalize legacy records if present
                        ev_text = item.get("Evidence") or item.get("content") or ""
                        ev_id = item.get("ID") or item.get("evidence_id") or ""
                        if not ev_id.startswith("EV/"):
                            ev_id = f"EV/{100000 + len(cleaned)}"
                        cleaned.append({
                            "ID": str(ev_id),
                            "Evidence": str(ev_text).strip()
                        })
                    return cleaned
            except Exception as e:
                print(f"[EvidenceManager] Error reading evidence pool: {e}")
                return []

    def _save_all(self, items: List[Dict[str, str]]) -> bool:
        # Strict validation: ONLY ID and Evidence allowed
        sanitized = []
        for it in items:
            sanitized.append({
                "ID": str(it.get("ID", "")),
                "Evidence": str(it.get("Evidence", "")).strip()
            })

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
            print(f"[EvidenceManager] Error saving evidence pool: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def _get_max_id_num(self, items: List[Dict[str, str]]) -> int:
        max_num = 99999  # So the first item gets 100000
        for item in items:
            item_id = item.get("ID", "")
            if item_id.startswith("EV/"):
                try:
                    num = int(item_id.split("/")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    pass
        return max_num

    def add_evidence(self, evidence: str) -> Dict[str, str]:
        """
        Adds clean evidence text to evidence_pool.json.
        Deduplicates if identical evidence text exists.
        Returns: {"ID": "EV/100000", "Evidence": "..."}
        """
        evidence_clean = evidence.strip()
        if not evidence_clean:
            return {}

        with self.lock:
            items = self.load_all()

            # Check duplicate evidence content
            for existing in items:
                if existing.get("Evidence", "").strip().lower() == evidence_clean.lower():
                    return existing

            max_num = self._get_max_id_num(items)
            new_id = f"EV/{max_num + 1}"
            
            new_item = {
                "ID": new_id,
                "Evidence": evidence_clean
            }
            items.append(new_item)
            self._save_all(items)
            return new_item

    def add_evidence_batch(self, evidence_list: List[str]) -> List[Dict[str, str]]:
        if not evidence_list:
            return []

        with self.lock:
            items = self.load_all()
            existing_texts = {it.get("Evidence", "").strip().lower() for it in items}
            
            added = []
            curr_id_num = self._get_max_id_num(items)

            for ev in evidence_list:
                ev_clean = ev.strip()
                if not ev_clean or ev_clean.lower() in existing_texts:
                    continue

                curr_id_num += 1
                new_id = f"EV/{curr_id_num}"
                new_item = {
                    "ID": new_id,
                    "Evidence": ev_clean
                }
                items.append(new_item)
                added.append(new_item)
                existing_texts.add(ev_clean.lower())

            if added:
                self._save_all(items)
            return added

    def get_count(self) -> int:
        return len(self.load_all())

    def query_items(
        self,
        search: Optional[str] = None,
        source_type: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str = "ID",
        sort_order: str = "desc"
    ) -> Tuple[List[Dict[str, str]], int]:
        items = self.load_all()

        if search and search.strip():
            q = search.strip().lower()
            items = [
                i for i in items
                if q in i.get("Evidence", "").lower()
                or q in i.get("ID", "").lower()
            ]

        total = len(items)
        reverse = (sort_order.lower() == "desc")
        items.sort(key=lambda x: x.get("ID", ""), reverse=reverse)

        return items[offset:offset + limit], total

    def export_data(self, format_type: str = "json") -> str:
        items = self.load_all()

        if format_type.lower() == "json":
            return json.dumps(items, indent=2, ensure_ascii=False)
        elif format_type.lower() == "jsonl":
            return "\n".join(json.dumps(i, ensure_ascii=False) for i in items)
        elif format_type.lower() == "csv":
            output = io.StringIO()
            fields = ["ID", "Evidence"]
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for item in items:
                writer.writerow({f: item.get(f, "") for f in fields})
            return output.getvalue()
        else:
            return json.dumps(items, indent=2, ensure_ascii=False)
