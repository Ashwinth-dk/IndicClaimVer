import logging
from typing import List, Dict, Any

from app.config import TOP_K, MIN_RELEVANCE_THRESHOLD

logger = logging.getLogger(__name__)

class EvidenceRanker:
    """
    Modular evidence ranker.
    Currently applies similarity score ranking and thresholding,
    designed for plug-and-play extension with cross-encoders or BM25 reranking.
    """

    def __init__(self, top_k: int = TOP_K, min_threshold: float = MIN_RELEVANCE_THRESHOLD):
        self.top_k = top_k
        self.min_threshold = min_threshold

    def rank(
        self,
        query: str,
        retrieved_candidates: List[Dict[str, Any]],
        top_k: int = None,
    ) -> List[Dict[str, Any]]:
        """
        Ranks and filters retrieved evidence candidates.
        Returns the top_k candidates in descending relevance order.
        """
        if not retrieved_candidates:
            return []

        limit = top_k if top_k is not None else self.top_k

        # Sort candidates by similarity_score in descending order
        sorted_candidates = sorted(
            retrieved_candidates,
            key=lambda x: x.get("similarity_score", 0.0),
            reverse=True,
        )

        # Select top-k and re-index ranks
        selected = []
        for i, item in enumerate(sorted_candidates[:limit], start=1):
            item_copy = dict(item)
            item_copy["rank"] = i
            selected.append(item_copy)

        return selected
