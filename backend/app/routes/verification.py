import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any

from app.models.schemas import ClaimRequest, VerificationResponse, HealthResponse
from app.config import (
    MODEL_PATH,
    EVIDENCE_POOL_PATH,
    EMBEDDING_MODEL_NAME,
    DEVICE,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Verification"])

# Global pipeline instance initialized on app lifespan
_pipeline = None

def get_pipeline():
    if _pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Verification pipeline is initializing. Please try again in a few seconds.",
        )
    return _pipeline

def set_pipeline(pipeline):
    global _pipeline
    _pipeline = pipeline

@router.post("/verify", response_model=VerificationResponse)
async def verify_claim_endpoint(
    request: ClaimRequest,
    pipeline = Depends(get_pipeline),
):
    """
    Verifies a factual claim across English, Tamil, Hindi, and Marathi:
    1. Preprocesses claim and detects language
    2. Retrieves candidate evidence passages via multilingual embeddings
    3. Ranks candidates
    4. Runs MuRIL sequence pair verification
    5. Returns overall verdict and detailed evidence analysis
    """
    if not request.claim or not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    try:
        response = pipeline.run(request.claim, expected_language=request.language)
        return response
    except Exception as e:
        logger.exception(f"Error during claim verification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}",
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns backend system status, device info, active model version, and loaded resources."""
    from app.storage.dataset_manager import DatasetManager
    from app.storage.review_manager import ReviewManager
    from app.config import MODEL_METADATA_PATH
    import json

    pipeline_ready = _pipeline is not None
    evidence_count = len(_pipeline.retriever.evidence_data) if pipeline_ready else 0
    
    active_version = "baseline"
    if MODEL_METADATA_PATH.exists():
        try:
            with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                active_version = meta.get("active_version", "baseline")
        except Exception:
            pass

    dm = DatasetManager()
    rm = ReviewManager()
    ds_stats = dm.get_stats()

    return HealthResponse(
        status="healthy" if pipeline_ready else "initializing",
        model="loaded" if pipeline_ready and _pipeline.verifier.model is not None else "pending",
        active_version=active_version,
        evidence_pool="loaded" if pipeline_ready and evidence_count > 0 else "pending",
        evidence_count=evidence_count,
        training_examples_count=ds_stats.get("total_count", 0),
        rejected_count=rm.get_count(),
        languages=ds_stats.get("languages", {}),
        device=str(DEVICE),
        embedding_model=EMBEDDING_MODEL_NAME,
    )


