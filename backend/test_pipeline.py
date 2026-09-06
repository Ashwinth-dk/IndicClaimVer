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

def test_inference():
    print("Initializing ClaimVerifier...")
    verifier = ClaimVerifier(
        model_path=MODEL_PATH,
        label_mapping_path=LABEL_MAPPING_PATH,
        device=DEVICE,
    )
    verifier.load_model()

    claim = "The Tamil Nadu government extended Covid-19 curbs."
    evidence = "The Tamil Nadu government on Monday extended the existing Covid-19 curbs till January 31 in view of rising cases."

    result = verifier.verify_pair(claim, evidence)
    print("MuRIL Verification Result:", result)
    assert "prediction" in result
    assert "confidence" in result
    print("ClaimVerifier test PASSED successfully!")

if __name__ == "__main__":
    test_inference()
