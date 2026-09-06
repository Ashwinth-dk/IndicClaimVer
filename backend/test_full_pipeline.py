import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.claim_verifier import ClaimVerifier
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.pipeline import VerificationPipeline
from app.config import (
    MODEL_PATH,
    LABEL_MAPPING_PATH,
    EVIDENCE_POOL_PATH,
    EMBEDDINGS_CACHE_PATH,
    EMBEDDING_MODEL_NAME,
    DEVICE,
)

def test_full_pipeline():
    print("1. Initializing EvidenceRetriever...")
    retriever = EvidenceRetriever(
        pool_path=EVIDENCE_POOL_PATH,
        cache_path=EMBEDDINGS_CACHE_PATH,
        model_name=EMBEDDING_MODEL_NAME,
        device=DEVICE,
    )
    retriever.build_index()
    print(f"Retriever indexed {len(retriever.evidence_data)} evidence passages.")

    print("2. Initializing Ranker and Verifier...")
    ranker = EvidenceRanker(top_k=5)
    verifier = ClaimVerifier(
        model_path=MODEL_PATH,
        label_mapping_path=LABEL_MAPPING_PATH,
        device=DEVICE,
    )
    verifier.load_model()

    print("3. Assembling Pipeline...")
    pipeline = VerificationPipeline(retriever, ranker, verifier)

    claim = "The Tamil Nadu government extended Covid-19 curbs till January 31."
    print(f"4. Running Pipeline for claim: '{claim}'...")
    response = pipeline.run(claim)

    print("\n================ PIPELINE RESULT ================")
    print("Claim:", response.claim)
    print("Verdict:", response.verdict)
    print("Confidence:", response.confidence)
    print("Supports Score:", response.supports_score)
    print("Refutes Score:", response.refutes_score)
    print("Summary:", response.summary)
    print("Retrieved Evidence Count:", len(response.evidence))
    for ev in response.evidence:
        print(f" - #{ev.rank} [{ev.id}] (Rel: {ev.retrieval_score*100:.1f}%, Pred: {ev.prediction}, Conf: {ev.confidence*100:.1f}%): {ev.text[:80]}...")
    print("=================================================")
    assert response.verdict in ["SUPPORTS", "REFUTES", "INSUFFICIENT_EVIDENCE"]
    print("FULL PIPELINE VERIFICATION PASSED!")

if __name__ == "__main__":
    test_full_pipeline()
