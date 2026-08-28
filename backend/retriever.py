import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.config import (
    EVIDENCE_POOL_PATH,
    INDEX_CACHE_PATH,
    RETRIEVER_MODEL_NAME,
    RETRIEVAL_TOP_K
)
from backend.data_pipeline import normalize_text

class EvidenceRetriever:
    """
    Hybrid Contextual Evidence Retriever:
    Combines dense semantic embeddings (Sentence Transformers) with lexical search (TF-IDF/BM25)
    to retrieve the most relevant evidence passages from the 53,000+ document pool.
    """
    def __init__(self, evidence_pool_path: Path = EVIDENCE_POOL_PATH, cache_dir: Path = INDEX_CACHE_PATH):
        self.evidence_pool_path = evidence_pool_path
        self.cache_dir = cache_dir
        self.passages: List[Dict[str, Any]] = []
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.dense_model = None
        self.dense_embeddings = None
        self.is_dense_ready = False
        
        self.load_corpus()
        self.build_tfidf_index()

    def load_corpus(self):
        """Loads passages from evidence_pool.json."""
        if not self.evidence_pool_path.exists():
            print(f"Warning: Evidence pool file {self.evidence_pool_path} not found.")
            return

        try:
            with open(self.evidence_pool_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
            self.passages = []
            for item in raw_data:
                ev_text = normalize_text(item.get("Evidence") or item.get("evidence") or "")
                if ev_text:
                    self.passages.append({
                        "id": str(item.get("ID") or item.get("id") or f"EV_{len(self.passages)}"),
                        "text": ev_text
                    })
            print(f"Loaded {len(self.passages)} evidence passages from pool.")
        except Exception as e:
            print(f"Error loading evidence corpus: {e}")

    def build_tfidf_index(self):
        """Builds an in-memory TF-IDF index for fast lexical matching and hybrid blending."""
        if not self.passages:
            return
        corpus_texts = [p["text"] for p in self.passages]
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=50000,
            sublinear_tf=True
        )
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(corpus_texts)
        print("TF-IDF Lexical Index ready.")

    def load_dense_model(self):
        """Lazily loads dense sentence transformer model."""
        if self.dense_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            print(f"Loading dense retriever model: {RETRIEVER_MODEL_NAME}...")
            self.dense_model = SentenceTransformer(RETRIEVER_MODEL_NAME)
            self.is_dense_ready = True
            print("Dense Sentence Transformer loaded successfully.")
        except Exception as e:
            print(f"Notice: SentenceTransformer loading fallback: {e}")
            self.dense_model = None
            self.is_dense_ready = False

    def retrieve(self, claim: str, top_k: int = RETRIEVAL_TOP_K) -> List[Dict[str, Any]]:
        """
        Retrieves top-k evidence passages for a given claim.
        Uses dense vector embeddings if loaded, blended with TF-IDF lexical scores.
        """
        claim_clean = normalize_text(claim)
        if not claim_clean or not self.passages:
            return []

        # 1. Lexical search scores
        claim_tfidf = self.tfidf_vectorizer.transform([claim_clean])
        lexical_scores = cosine_similarity(claim_tfidf, self.tfidf_matrix).flatten()

        # 2. Dense semantic scores if available
        if self.dense_model is not None:
            try:
                # Retrieve top-50 lexical candidates first for fast re-ranking
                candidate_indices = np.argsort(lexical_scores)[-50:][::-1]
                candidate_texts = [self.passages[idx]["text"] for idx in candidate_indices]
                
                claim_emb = self.dense_model.encode([claim_clean], normalize_embeddings=True)
                cand_embs = self.dense_model.encode(candidate_texts, normalize_embeddings=True)
                
                dense_scores = np.dot(cand_embs, claim_emb.T).flatten()
                
                # Hybrid score: 0.7 * Dense + 0.3 * Lexical
                combined = []
                for i, idx in enumerate(candidate_indices):
                    lex_score = float(lexical_scores[idx])
                    den_score = float(dense_scores[i])
                    final_score = 0.75 * den_score + 0.25 * lex_score
                    combined.append((idx, final_score))
                
                combined.sort(key=lambda x: x[1], reverse=True)
                top_indices = combined[:top_k]
                
                results = []
                for idx, score in top_indices:
                    results.append({
                        "id": self.passages[idx]["id"],
                        "evidence": self.passages[idx]["text"],
                        "score": round(float(score), 4),
                        "retrieval_mode": "hybrid_dense_lexical"
                    })
                return results
            except Exception as e:
                print(f"Dense retrieval error, falling back to lexical: {e}")

        # Lexical-only fallback
        top_indices = np.argsort(lexical_scores)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                "id": self.passages[idx]["id"],
                "evidence": self.passages[idx]["text"],
                "score": round(float(lexical_scores[idx]), 4),
                "retrieval_mode": "lexical_tfidf"
            })
        return results

    def add_passages(self, new_passages: List[Dict[str, Any]]):
        """Dynamically adds newly crawled passages and refreshes index."""
        added = 0
        existing_ids = {p["id"] for p in self.passages}
        for item in new_passages:
            pid = str(item.get("id") or item.get("ID") or f"crawled_{len(self.passages)}")
            text = normalize_text(item.get("text") or item.get("evidence") or item.get("Evidence") or "")
            if text and pid not in existing_ids:
                self.passages.append({"id": pid, "text": text})
                existing_ids.add(pid)
                added += 1
        if added > 0:
            self.build_tfidf_index()
            print(f"Appended {added} new passages to retriever index. Total: {len(self.passages)}")

# Global singleton
_retriever_instance: Optional[EvidenceRetriever] = None

def get_retriever() -> EvidenceRetriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = EvidenceRetriever()
    return _retriever_instance
