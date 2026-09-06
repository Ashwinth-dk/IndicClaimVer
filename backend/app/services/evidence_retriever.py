import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import (
    EVIDENCE_POOL_PATH,
    EMBEDDINGS_CACHE_PATH,
    EMBEDDING_MODEL_NAME,
    DEVICE,
)
from app.utils.preprocessing import normalize_indic_text

logger = logging.getLogger(__name__)

class EvidenceRetriever:
    """
    Modular evidence retriever using multilingual sentence embeddings
    and fast vector cosine similarity.
    """

    def __init__(
        self,
        pool_path: Path = EVIDENCE_POOL_PATH,
        cache_path: Path = EMBEDDINGS_CACHE_PATH,
        model_name: str = EMBEDDING_MODEL_NAME,
        device: str = DEVICE,
    ):
        self.pool_path = Path(pool_path)
        self.cache_path = Path(cache_path)
        self.model_name = model_name
        self.device = device
        
        self.model: Optional[SentenceTransformer] = None
        self.evidence_data: List[Dict[str, str]] = []  # [{ "id": "...", "text": "..." }]
        self.embeddings: Optional[np.ndarray] = None   # shape: (N, D), normalized

    def load_evidence(self) -> List[Dict[str, str]]:
        """Loads and normalizes evidence items from evidence_pool.json."""
        logger.info(f"Loading evidence pool from {self.pool_path}...")
        if not self.pool_path.exists():
            raise FileNotFoundError(f"Evidence pool not found at {self.pool_path}")

        with open(self.pool_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        cleaned_data = []
        for item in raw_data:
            eid = str(item.get("ID") or item.get("id") or item.get("evidence_id") or f"EV_{len(cleaned_data)}")
            raw_text = str(item.get("Evidence") or item.get("evidence") or item.get("text") or "")
            cleaned_text = normalize_indic_text(raw_text)
            if cleaned_text:
                cleaned_data.append({"id": eid, "text": cleaned_text})

        self.evidence_data = cleaned_data
        logger.info(f"Successfully loaded {len(self.evidence_data)} evidence passages.")
        return self.evidence_data

    def build_index(self, force_recompute: bool = False):
        """Loads embedding model, builds or loads cached embeddings."""
        if not self.evidence_data:
            self.load_evidence()

        logger.info(f"Initializing embedding model '{self.model_name}' on device '{self.device}'...")
        self.model = SentenceTransformer(self.model_name, device=self.device)

        # Check for valid cache
        cache_valid = False
        if not force_recompute and self.cache_path.exists():
            try:
                logger.info(f"Loading precomputed evidence embeddings from cache: {self.cache_path}")
                cached = np.load(self.cache_path, allow_pickle=True)
                cached_embs = cached["embeddings"]
                cached_ids = cached["ids"]
                if len(cached_embs) == len(self.evidence_data):
                    self.embeddings = cached_embs.astype(np.float32)
                    cache_valid = True
                    logger.info("Cached embeddings loaded and verified successfully.")
                else:
                    logger.warning("Cache size mismatch. Recomputing embeddings...")
            except Exception as e:
                logger.warning(f"Failed to read cache ({e}). Recomputing embeddings...")

        if not cache_valid:
            logger.info(f"Encoding {len(self.evidence_data)} evidence passages (this runs once and is cached)...")
            texts = [item["text"] for item in self.evidence_data]
            embs = self.model.encode(
                texts,
                batch_size=64,
                show_progress_bar=True,
                normalize_embeddings=True,
                device=self.device,
            )
            self.embeddings = np.array(embs, dtype=np.float32)

            try:
                self.cache_path.parent.mkdir(parents=True, exist_ok=True)
                ids = np.array([item["id"] for item in self.evidence_data])
                np.savez_compressed(self.cache_path, embeddings=self.embeddings, ids=ids)
                logger.info(f"Saved computed embeddings to {self.cache_path}")
            except Exception as e:
                logger.warning(f"Could not persist embeddings cache: {e}")

    def retrieve(self, query: str, top_k: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieves top_k relevant evidence items for a given claim query
        using semantic cosine similarity.
        """
        if self.model is None or self.embeddings is None:
            raise RuntimeError("EvidenceRetriever index not built. Call build_index() first.")

        cleaned_query = normalize_indic_text(query)
        if not cleaned_query:
            return []

        # Encode query
        query_emb = self.model.encode(
            cleaned_query,
            normalize_embeddings=True,
            device=self.device,
        )
        query_emb = np.array(query_emb, dtype=np.float32)

        # Compute cosine similarity (dot product of normalized vectors)
        scores = np.dot(self.embeddings, query_emb)

        # Retrieve top indices
        top_k = min(top_k, len(self.evidence_data))
        if top_k <= 0:
            return []

        # Get top-k indices in descending order
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, start=1):
            item = self.evidence_data[idx]
            sim_score = float(scores[idx])
            # Clamp similarity score between 0.0 and 1.0 for normalized clarity
            normalized_score = max(0.0, min(1.0, (sim_score + 1.0) / 2.0 if sim_score < 0 else sim_score))
            results.append({
                "rank": rank,
                "id": item["id"],
                "text": item["text"],
                "similarity_score": round(normalized_score, 4),
                "raw_cosine": round(sim_score, 4),
            })

        return results
