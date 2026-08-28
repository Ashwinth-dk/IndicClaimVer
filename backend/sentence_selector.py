import re
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.data_pipeline import normalize_text
from backend.config import SENTENCE_TOP_K

def split_sentences(text: str) -> List[str]:
    """
    Splits multilingual text into sentences supporting English, Hindi, Bengali, etc.
    Handles delimiters: ., !, ?, ।, ||, newline.
    """
    text = normalize_text(text)
    # Split by standard sentence terminators including Indic danda '।' and '॥'
    raw_sentences = re.split(r'(?<=[.!?।॥\n])\s+', text)
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
    if not sentences and text:
        sentences = [text]
    return sentences

class SentenceSelector:
    """
    Extracts the most salient evidence sentence(s) from a retrieved passage
    to serve as the final decisive rationale for claim verification.
    """
    def __init__(self):
        self.dense_model = None

    def load_dense_model(self):
        if self.dense_model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            from backend.config import SENTENCE_SELECTOR_MODEL
            self.dense_model = SentenceTransformer(SENTENCE_SELECTOR_MODEL)
        except Exception as e:
            self.dense_model = None

    def select_salient_sentences(
        self,
        claim: str,
        passage: str,
        top_k: int = SENTENCE_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Ranks sentences in the passage by relevance to the claim.
        Returns sorted list of {sentence, score, rank}.
        """
        claim_clean = normalize_text(claim)
        sentences = split_sentences(passage)
        if not sentences or not claim_clean:
            return []

        # If only 1 sentence in passage, return it directly
        if len(sentences) == 1:
            return [{
                "sentence": sentences[0],
                "score": 1.0,
                "rank": 1
            }]

        # Semantic ranking with Dense model if available
        if self.dense_model is not None:
            try:
                claim_emb = self.dense_model.encode([claim_clean], normalize_embeddings=True)
                sent_embs = self.dense_model.encode(sentences, normalize_embeddings=True)
                scores = np.dot(sent_embs, claim_emb.T).flatten()
                
                ranked_indices = np.argsort(scores)[::-1][:top_k]
                results = []
                for rank, idx in enumerate(ranked_indices, start=1):
                    results.append({
                        "sentence": sentences[idx],
                        "score": round(float(scores[idx]), 4),
                        "rank": rank
                    })
                return results
            except Exception as e:
                print(f"Dense sentence selector fallback: {e}")

        # Lexical TF-IDF ranking fallback
        try:
            corpus = [claim_clean] + sentences
            vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
            tfidf = vectorizer.fit_transform(corpus)
            scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
            
            ranked_indices = np.argsort(scores)[::-1][:top_k]
            results = []
            for rank, idx in enumerate(ranked_indices, start=1):
                results.append({
                    "sentence": sentences[idx],
                    "score": round(float(scores[idx]), 4),
                    "rank": rank
                })
            return results
        except Exception:
            return [{"sentence": sentences[0], "score": 0.5, "rank": 1}]

# Global singleton
_selector_instance: Optional[SentenceSelector] = None

def get_sentence_selector() -> SentenceSelector:
    global _selector_instance
    if _selector_instance is None:
        _selector_instance = SentenceSelector()
    return _selector_instance
