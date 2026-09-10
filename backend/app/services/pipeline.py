import logging
import unicodedata
from typing import Dict, Any, List, Optional

from app.config import TOP_K, INITIAL_RETRIEVAL_K, MIN_RELEVANCE_THRESHOLD
from app.utils.preprocessing import preprocess_claim
from app.utils.language_detector import LanguageDetector
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.claim_verifier import ClaimVerifier
from app.models.schemas import VerificationResponse, EvidenceItem, ProcessingStatus

logger = logging.getLogger(__name__)

class VerificationPipeline:
    """
    End-to-end Multilingual Claim Verification Pipeline coordinating:
    1. Multilingual Claim Preprocessing & Language Detection (EN, TA, HI, MR)
    2. Semantic Evidence Retrieval (Top-20 via multilingual sentence transformer)
    3. Evidence Ranking & Relevance Filtering (Top-5)
    4. Fine-Tuned MuRIL Sequence Pair Classification
    5. Weighted Relevance-Aware Aggregation & Localized Verdict Formulation
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
        language: str = "en"
    ) -> str:
        """Generates a natural summary adapted for the detected language."""
        count = len(evidence_items)
        conf_pct = int(round(confidence * 100))

        if verdict == "INSUFFICIENT_EVIDENCE" or count == 0:
            if language == "ta":
                return "இந்த கூற்றை சரிபார்க்க போதுமான ஆதாரங்கள் கிடைக்கவில்லை. தயவுசெய்து கூற்றை சற்று விரிவாக குறிப்பிடவும்."
            elif language == "hi":
                return "इस दावे को सत्यापित करने के लिए पर्याप्त प्रासंगिक साक्ष्य नहीं मिले। कृपया दावे को अधिक स्पष्ट रूप से प्रस्तुत करें।"
            elif language == "mr":
                return "या दाव्याची पडताळणी करण्यासाठी पुरेसे पुरावे उपलब्ध नाहीत. कृपया दाव्यात अधिक माहिती द्या."
            else:
                return (
                    "Insufficient relevant evidence was discovered in the current evidence pool to verify this claim with high certainty. "
                    "Please consider refining or broadening the factual statement."
                )

        num_supports = sum(1 for e in evidence_items if e["prediction"] == "SUPPORTS")
        num_refutes = sum(1 for e in evidence_items if e["prediction"] == "REFUTES")
        top_evidence = evidence_items[0]
        top_conf_pct = int(round(top_evidence["confidence"] * 100))

        if language == "ta":
            action = "உறுதிப்படுத்தப்பட்டுள்ளது (ஆதரிக்கப்படுகிறது)" if verdict == "SUPPORTS" else "மறுக்கப்பட்டுள்ளது (பொய்யானது)"
            return f"ஆதாரங்களின் அடிப்படையில், இந்த கூற்று **{action}** ({conf_pct}% உறுதித்தன்மை). கணினி {count} ஆதாரங்களை மதிப்பாய்வு செய்தது ({num_supports} ஆதரவு, {num_refutes} மறுப்பு)."
        elif language == "hi":
            action = "समर्थित है (सही)" if verdict == "SUPPORTS" else "खंडित है (गलत)"
            return f"उपलब्ध साक्ष्यों के आधार पर, यह दावा **{action}** ({conf_pct}% विश्वसनीयता). प्रणाली ने {count} साक्ष्यों का मूल्यांकन किया ({num_supports} समर्थन, {num_refutes} खंडन)."
        elif language == "mr":
            action = "पुष्टी झाली आहे (सत्य)" if verdict == "SUPPORTS" else "फेटाळण्यात आला आहे (असत्य)"
            return f"उपलब्ध पुराव्यांच्या आधारे, हा दावा **{action}** ({conf_pct}% खात्री). प्रणालीने {count} पुराव्यांची तपासणी केली ({num_supports} समर्थन, {num_refutes} नकार)."
        else:
            if verdict == "SUPPORTS":
                return (
                    f"Based on the retrieved evidence, the claim is **supported** with **{conf_pct}% confidence**. "
                    f"The system evaluated {count} relevant evidence passages ({num_supports} supporting, {num_refutes} refuting). "
                    f"The highest-ranked passage (ID: {top_evidence['id']}) affirms the claim with {top_conf_pct}% certainty."
                )
            else:
                return (
                    f"Based on the retrieved evidence, the claim is **refuted** with **{conf_pct}% confidence**. "
                    f"The system evaluated {count} relevant evidence passages ({num_refutes} refuting, {num_supports} supporting). "
                    f"The highest-ranked passage (ID: {top_evidence['id']}) contradicts the claim with {top_conf_pct}% certainty."
                )

    def run(self, raw_claim: str, expected_language: Optional[str] = None) -> VerificationResponse:
        """Executes the full multilingual pipeline for a given user claim."""
        cleaned_claim = preprocess_claim(raw_claim)
        if not cleaned_claim:
            return VerificationResponse(
                claim=raw_claim,
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                supports_score=0.0,
                refutes_score=0.0,
                summary="The submitted claim is empty or contains no readable text.",
                language="en",
                evidence=[],
                processing=ProcessingStatus(
                    claim_analysis="completed",
                    evidence_retrieval="failed",
                    evidence_ranking="skipped",
                    verification="skipped",
                ),
            )

        # Detect language
        lang_res = LanguageDetector.detect_language(cleaned_claim)
        detected_lang = lang_res["language"] if lang_res["language"] != "und" else (expected_language or "en")
        lang_conf = lang_res["confidence"]

        # Step 1: Initial Retrieval (Top 20 candidates from multilingual evidence pool)
        candidates = self.retriever.retrieve(cleaned_claim, top_k=INITIAL_RETRIEVAL_K)

        # Step 2: Ranking (Select Top-K relevant candidates)
        ranked_evidence = self.ranker.rank(cleaned_claim, candidates, top_k=TOP_K)

        # Check for insufficient evidence
        if not ranked_evidence or (
            ranked_evidence[0].get("similarity_score", 0.0) < MIN_RELEVANCE_THRESHOLD
        ):
            logger.info(f"Insufficient relevant evidence for claim: '{cleaned_claim}' ({detected_lang})")
            return VerificationResponse(
                claim=cleaned_claim,
                verdict="INSUFFICIENT_EVIDENCE",
                confidence=0.0,
                supports_score=0.0,
                refutes_score=0.0,
                summary=self.generate_summary(cleaned_claim, "INSUFFICIENT_EVIDENCE", 0.0, [], language=detected_lang),
                language=detected_lang,
                language_confidence=lang_conf,
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
            language=detected_lang
        )

        active_version = "baseline"
        if hasattr(self.verifier, "model_path") and self.verifier.model_path:
            v_name = self.verifier.model_path.name
            active_version = v_name.replace("muril_claim_verification_model_", "") if "muril_claim_verification_model_" in v_name else "baseline"

        return VerificationResponse(
            claim=cleaned_claim,
            verdict=final_verdict,
            confidence=round(final_confidence, 4),
            supports_score=round(overall_supports, 4),
            refutes_score=round(overall_refutes, 4),
            summary=summary,
            language=detected_lang,
            language_confidence=lang_conf,
            model_version=active_version,
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
