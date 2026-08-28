import json
import re
import unicodedata
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sklearn.model_selection import StratifiedKFold
from backend.config import (
    TRAIN_DATA_PATH,
    DEV_DATA_PATH,
    CRAWLED_DATA_PATH,
    LABEL2ID,
    ID2LABEL
)

def normalize_text(text: str) -> str:
    """
    Cleans text by normalizing unicode characters (NFKC),
    stripping invisible zero-width chars, and standardizing whitespace.
    """
    if not isinstance(text, str):
        text = str(text or "")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u200b", "").replace("\ufeff", "").replace("\r\n", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def canonical_label(label: Any) -> str:
    """
    Maps various rating strings to standard SUPPORTS, REFUTES, or NOT ENOUGH INFO.
    """
    if not isinstance(label, str):
        return "NOT ENOUGH INFO"
    lbl = label.strip().upper()
    
    if lbl in ["SUPPORTS", "SUPPORT", "TRUE", "CORRECT", "MOSTLY TRUE", "VERIFIED"]:
        return "SUPPORTS"
    if lbl in ["REFUTES", "REFUTE", "FALSE", "MISLEADING", "FAKE", "PANTS ON FIRE", "INCORRECT", "DEBUNKED", "UNTRUE"]:
        return "REFUTES"
    if lbl in ["NOT ENOUGH INFO", "NOT ENOUGH INFORMATION", "NEI", "UNVERIFIED", "MIXTURE", "HALF TRUE", "UNPROVEN"]:
        return "NOT ENOUGH INFO"
    
    # Heuristic substring checks
    if "FALSE" in lbl or "REFUTE" in lbl or "FAKE" in lbl or "MISLEAD" in lbl:
        return "REFUTES"
    if "TRUE" in lbl or "SUPPORT" in lbl or "ACCURATE" in lbl:
        return "SUPPORTS"
        
    return "NOT ENOUGH INFO"

def load_json_records(path: Path) -> List[Dict[str, Any]]:
    """Loads JSON file containing list of records."""
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as e:
        print(f"Error loading {path}: {e}")
        return []

def load_and_preprocess_dataset(
    include_crawled: bool = True,
    train_path: Path = TRAIN_DATA_PATH,
    dev_path: Path = DEV_DATA_PATH,
    crawled_path: Path = CRAWLED_DATA_PATH
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads train and dev datasets with optional crawled dataset merging,
    cleans texts, normalizes labels, and returns cleaned DataFrames.
    """
    train_records = load_json_records(train_path)
    dev_records = load_json_records(dev_path)
    
    def process_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = []
        for item in records:
            claim = normalize_text(item.get("Text") or item.get("claim") or item.get("Claim") or "")
            evidence = normalize_text(item.get("Evidence") or item.get("evidence") or "")
            raw_label = item.get("Label") or item.get("label") or "NOT ENOUGH INFO"
            label_str = canonical_label(raw_label)
            
            if claim and evidence:
                rows.append({
                    "id": str(item.get("ID") or item.get("id") or f"gen_{len(rows)}"),
                    "claim": claim,
                    "evidence": evidence,
                    "label_str": label_str,
                    "label": LABEL2ID[label_str]
                })
        return rows

    train_rows = process_records(train_records)
    dev_rows = process_records(dev_records)

    # Optionally merge crawled data into training set
    if include_crawled and crawled_path.exists():
        crawled_records = load_json_records(crawled_path)
        crawled_rows = process_records(crawled_records)
        print(f"Incorporating {len(crawled_rows)} crawled samples into training data.")
        train_rows.extend(crawled_rows)

    train_df = pd.DataFrame(train_rows).drop_duplicates(subset=["claim", "evidence"])
    dev_df = pd.DataFrame(dev_rows).drop_duplicates(subset=["claim", "evidence"])

    return train_df, dev_df

def get_kfold_splits(df: pd.DataFrame, n_splits: int = 5, seed: int = 42):
    """
    Generates stratified K-Fold splits for robust cross-validation.
    """
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return skf.split(df, df["label"])

def get_dataset_statistics() -> Dict[str, Any]:
    """Computes comprehensive dataset metrics across all splits."""
    train_df, dev_df = load_and_preprocess_dataset(include_crawled=True)
    crawled_count = len(load_json_records(CRAWLED_DATA_PATH))
    
    train_counts = train_df["label_str"].value_counts().to_dict()
    dev_counts = dev_df["label_str"].value_counts().to_dict()
    
    return {
        "train_samples": len(train_df),
        "dev_samples": len(dev_df),
        "crawled_samples": crawled_count,
        "train_label_distribution": train_counts,
        "dev_label_distribution": dev_counts,
        "languages_detected": ["Hindi", "Bengali", "English", "Tamil", "Multi-lingual Indic"]
    }
