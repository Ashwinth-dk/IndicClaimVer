import json
import os
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path


class SourceManager:
    """
    Manages the source registry (source_registry.json).
    Allows enabling/disabling sources, adding custom sources, and filtering.
    """
    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path:
            self.file_path = Path(data_file_path)
        else:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.file_path = base_dir / "data" / "source_registry.json"
        
        self.lock = threading.RLock()
        self._ensure_file_exists()


    def _ensure_file_exists(self):
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists() or self.file_path.stat().st_size <= 5:
            if not self.file_path.exists():
                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump([], f, indent=2, ensure_ascii=False)

    def load_all(self) -> List[Dict[str, Any]]:
        with self.lock:
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[SourceManager] Error reading source registry: {e}")
                return []

    def _save_all(self, items: List[Dict[str, Any]]) -> bool:
        temp_path = self.file_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
            return True
        except Exception as e:
            print(f"[SourceManager] Error saving source registry: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def get_enabled_sources(self, source_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        sources = self.load_all()
        enabled = [s for s in sources if s.get("enabled", True)]
        if source_types:
            types_lower = [t.lower() for t in source_types]
            enabled = [s for s in enabled if s.get("source_type", "").lower() in types_lower]
        return enabled

    def toggle_source(self, source_id: str, enabled: bool) -> Optional[Dict[str, Any]]:
        with self.lock:
            sources = self.load_all()
            found = None
            for s in sources:
                if s.get("source_id") == source_id:
                    s["enabled"] = enabled
                    found = s
                    break
            if found:
                self._save_all(sources)
            return found

    def add_source(
        self,
        source_name: str,
        base_url: str,
        source_type: str,
        reliability_score: float = 0.9,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        with self.lock:
            sources = self.load_all()
            
            clean_name = "".join(c for c in source_name if c.isalnum())[:8].upper()
            source_id = f"SRC_{clean_name}_{len(sources)+1}"
            
            new_source = {
                "source_id": source_id,
                "source_name": source_name.strip(),
                "base_url": base_url.strip(),
                "source_type": source_type.lower(),
                "enabled": True,
                "reliability_score": min(1.0, max(0.0, reliability_score)),
                "description": description or f"User registered {source_type} source"
            }
            sources.append(new_source)
            self._save_all(sources)
            return new_source

    def delete_source(self, source_id: str) -> bool:
        with self.lock:
            sources = self.load_all()
            init_len = len(sources)
            sources = [s for s in sources if s.get("source_id") != source_id]
            if len(sources) < init_len:
                self._save_all(sources)
                return True
            return False
