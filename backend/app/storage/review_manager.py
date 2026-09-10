import json
import os
import io
import csv
import threading
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from datetime import datetime


class ReviewManager:
    """
    Manages rejected examples and candidate items pending manual review (rejected_examples.json).
    Allows inspecting reasons for rejection and manually approving/editing items.
    """
    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path:
            self.file_path = Path(data_file_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.file_path = base_dir / "data" / "rejected_examples.json"
        
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
                    return json.load(f)
            except Exception as e:
                print(f"[ReviewManager] Error reading rejected examples: {e}")
                return []

    def _save_all(self, items: List[Dict[str, Any]]) -> bool:
        temp_path = self.file_path.with_name(f"{self.file_path.stem}_{os.getpid()}_{threading.get_ident()}.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            
            # Windows safe replace
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
            # Direct overwrite fallback
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return True
        except Exception as e:
            print(f"[ReviewManager] Error saving rejected examples: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def _get_max_id_num(self, items: List[Dict[str, Any]]) -> int:
        max_num = 0
        for item in items:
            item_id = str(item.get("ID", ""))
            if item_id.startswith("REJECTED/"):
                try:
                    num = int(item_id.split("/")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    pass
            elif item_id.startswith("R1/"):
                try:
                    num = int(item_id.split("/")[1])
                    if num > max_num:
                        max_num = num
                except (IndexError, ValueError):
                    pass
        return max_num

    def add_rejected(
        self,
        text: str,
        evidence: str,
        reason: str,
        confidence: Optional[float] = None,
        proposed_label: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        with self.lock:
            items = self.load_all()
            max_num = self._get_max_id_num(items)
            item_id = f"REJECTED/{max_num + 1:06d}"
            
            new_item = {
                "ID": item_id,
                "Text": text.strip(),
                "Evidence": evidence.strip(),
                "Reason": reason.strip(),
                "Confidence": confidence,
                "ProposedLabel": proposed_label,
                "Timestamp": datetime.now().isoformat(),
                "Metadata": metadata or {}
            }
            items.append(new_item)
            self._save_all(items)
            return new_item

    def get_count(self) -> int:
        return len(self.load_all())

    def query_items(
        self,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50
    ) -> Tuple[List[Dict[str, Any]], int]:
        items = self.load_all()
        if search and search.strip():
            q = search.strip().lower()
            items = [
                i for i in items
                if q in i.get("Text", "").lower()
                or q in i.get("Evidence", "").lower()
                or q in i.get("Reason", "").lower()
                or q in i.get("ID", "").lower()
            ]
        total = len(items)
        items.sort(key=lambda x: x.get("Timestamp", ""), reverse=True)
        return items[offset:offset + limit], total

    def pop_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            items = self.load_all()
            found = None
            new_items = []
            for item in items:
                if item.get("ID") == item_id and found is None:
                    found = item
                else:
                    new_items.append(item)
            if found:
                self._save_all(new_items)
            return found

    def delete_item(self, item_id: str) -> bool:
        with self.lock:
            items = self.load_all()
            init_len = len(items)
            items = [i for i in items if i.get("ID") != item_id]
            if len(items) < init_len:
                self._save_all(items)
                return True
            return False

    def export_data(self, format_type: str = "json") -> str:
        items = self.load_all()
        if format_type.lower() == "json":
            return json.dumps(items, indent=2, ensure_ascii=False)
        elif format_type.lower() == "jsonl":
            return "\n".join(json.dumps(i, ensure_ascii=False) for i in items)
        elif format_type.lower() == "csv":
            output = io.StringIO()
            fields = ["ID", "Text", "Evidence", "Reason", "Confidence", "Timestamp"]
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for item in items:
                writer.writerow({
                    "ID": item.get("ID", ""),
                    "Text": item.get("Text", ""),
                    "Evidence": item.get("Evidence", ""),
                    "Reason": item.get("Reason", ""),
                    "Confidence": item.get("Confidence", ""),
                    "Timestamp": item.get("Timestamp", "")
                })
            return output.getvalue()
        else:
            return json.dumps(items, indent=2, ensure_ascii=False)
