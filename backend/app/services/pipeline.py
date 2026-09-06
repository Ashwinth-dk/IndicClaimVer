import logging
from typing import Dict, Any, List

from app.config import TOP_K, INITIAL_RETRIEVAL_K, MIN_RELEVANCE_THRESHOLD
from app.utils.preprocessing import preprocess_claim
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.claim_verifier import ClaimVerifier
from app.models.schemas import VerificationResponse, EvidenceItem, ProcessingStatus

logger = logging.getLogger(__name__)

class VerificationPipeline:
    """
    End-to-end Claim Verification Pipeline coordinating:
    1. Claim Preprocessing
    2. Semantic Evidence Retrieval (Top-20)
    3. Evidence Ranking & Filtering (Top-5)
    4. Fine-Tuned MuRIL Sequence Pair Classification
    5. Weighted Relevance-Aware Aggregation & Verdict Formulation
    """

    def __init__(
        self,
        retriever: EvidenceRetriever,
        ranker: EvidenceRanker,
        verifier: ClaimVerifier,
    ):
        self.retriever = retriever
        self.ranker = ranker
        self.verifier = verifier

    def generate_summary(
        self,
        claim: str,
        verdict: str,
        confidence: float,
        evidence_items: List[Dict[str, Any]],
    ) -> str:
        """Generates a natural, conversational research assistant summary."""
        count = len(evidence_items)
        if verdict == "INSUFFICIENT_EVIDENCE" or count == 0:
            return (
                "Insufficient relevant evidence was discovered in the current evidence pool to verify this claim with high certainty. "
                "Please consider refining or broadening the factual statement."
            )

        conf_pct = int(round(confidence * 100))
        verdict_lower = verdict.lower()
        
        # Count supporting and refuting passages
        num_supports = sum(1 for e in evidence_items if e["prediction"] == "SUPPORTS")
        num_refutes = sum(1 for e in evidence_items if e["prediction"] == "REFUTES")

        top_evidence = evidence_items[0]
        top_conf_pct = int(round(top_evidence["confidence"] * 100))

        if verdict == "SUPPORTS":
            text = (
                f"Based on the retrieved evidence, the claim is **supported** with **{conf_pct}% confidence**. "
                f"The system evaluated {count} relevant evidence passages ({num_supports} supporting, {num_refutes} refuting). "
                f"The highest-ranked passage (ID: {top_evidence['id']}) affirms the claim with {top_conf_pct}% verification certainty."
            )
        else:
            text = (
                f"Based on the retrieved evidence, the claim is **refuted** with **{conf_pct}% confidence**. "
                f"The system evaluated {count} relevant evidence passages ({num_refutes} refuting, {num_supports} supporting). "
                f"The highest-ranked passage (ID: {top_evidence['id']}) contradicts the claim with {top_conf_pct}% verification certainty."
            )

        return text

    def run(self, raw_claim: str) -> VerificationResponse:
        """Executes the full pipeline for a given user claim."""
        cleaned_claim = preprocess_claim(raw_claim)
        if not cleaned_claim:
            return VerificationResponse(
                claim=raw_claim,
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                supports_score=0.0,
                refutes_score=0.0,
                summary="The submitted claim is empty or contains no readable text.",
                evidence=[],
                processing=ProcessingStatus(
                    claim_analysis="completed",
                    evidence_retrieval="failed",
                    evidence_ranking="skipped",
                    verification="skipped",
                ),
            )

        # Step 1: Initial Retrieval (Top 20 candidates)
        candidates = self.retriever.retrieve(cleaned_claim, top_k=INITIAL_RETRIEVAL_K)

        # Step 2: Ranking (Select Top-K relevant candidates)
        ranked_evidence = self.ranker.rank(cleaned_claim, candidates, top_k=TOP_K)

        # Check for insufficient evidence
        if not ranked_evidence or (
            ranked_evidence[0].get("similarity_score", 0.0) < MIN_RELEVANCE_THRESHOLD
        ):
            logger.info(f"Insufficient relevant evidence for claim: '{cleaned_claim}'")
            return VerificationResponse(
                claim=cleaned_claim,
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                supports_score=0.0,
                refutes_score=0.0,
                summary="Insufficient relevant evidence found in the database for reliable verification.",
                evidence=[
                    EvidenceItem(
                        rank=item["rank"],
                        id=item["id"],
                        text=item["text"],
                        retrieval_score=item["similarity_score"],
                        prediction="N/A",
                        confidence=0.0,
                    )
                    for item in ranked_evidence[:3]
                ],
                processing=ProcessingStatus(),
            )

        # Step 3: MuRIL Sequence Pair Verification for each evidence
        evidence_results: List[Dict[str, Any]] = []
        weighted_supports = 0.0
        weighted_refutes = 0.0
        total_weight = 0.0

        for item in ranked_evidence:
            prediction_result = self.verifier.verify_pair(
                claim=cleaned_claim,
                evidence=item["text"],
            )

            retrieval_score = float(item.get("similarity_score", 0.5))
            # Weight is scaled by retrieval similarity score (with minimum floor to avoid zero division)
            weight = max(0.05, retrieval_score)
            total_weight += weight

            weighted_supports += weight * prediction_result["supports_prob"]
            weighted_refutes += weight * prediction_result["refutes_prob"]

            evidence_results.append({
                "rank": item["rank"],
                "id": item["id"],
                "text": item["text"],
                "retrieval_score": retrieval_score,
                "prediction": prediction_result["prediction"],
                "confidence": prediction_result["confidence"],
            })

        # Step 4: Overall Verdict Aggregation
        if total_weight > 0:
            overall_supports = weighted_supports / total_weight
            overall_refutes = weighted_refutes / total_weight
        else:
            overall_supports = 0.5
            overall_refutes = 0.5

        if overall_supports >= overall_refutes:
            final_verdict = "SUPPORTS"
            final_confidence = overall_supports
        else:
            final_verdict = "REFUTES"
            final_confidence = overall_refutes

        # Step 5: Summary Generation
        summary = self.generate_summary(
            claim=cleaned_claim,
            verdict=final_verdict,
            confidence=final_confidence,
            evidence_items=evidence_results,
        )

        return VerificationResponse(
            claim=cleaned_claim,
            verdict=final_verdict,
            confidence=round(final_confidence, 4),
            supports_score=round(overall_supports, 4),
            refutes_score=round(overall_refutes, 4),
            summary=summary,
            evidence=[
                EvidenceItem(
                    rank=e["rank"],
                    id=e["id"],
                    text=e["text"],
                    retrieval_score=e["retrieval_score"],
                    prediction=e["prediction"],
                    confidence=e["confidence"],
                )
                for e in evidence_results
            ],
            processing=ProcessingStatus(
                claim_analysis="completed",
                evidence_retrieval="completed",
                evidence_ranking="completed",
                verification="completed",
            ),
        )
