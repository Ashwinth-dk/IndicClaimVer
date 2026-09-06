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
    Verifies a factual claim:
    1. Preprocesses claim
    2. Retrieves candidate evidence passages
    3. Ranks candidates
    4. Runs MuRIL claim verification
    5. Returns overall verdict and detailed evidence analysis
    """
    if not request.claim or not request.claim.strip():
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    try:
        response = pipeline.run(request.claim)
        return response
    except Exception as e:
        logger.exception(f"Error during claim verification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Verification failed: {str(e)}",
        )

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns backend system status, device info, and loaded resources."""
    pipeline_ready = _pipeline is not None
    evidence_count = len(_pipeline.retriever.evidence_data) if pipeline_ready else 0
    
    return HealthResponse(
        status="healthy" if pipeline_ready else "initializing",
        model="loaded" if pipeline_ready and _pipeline.verifier.model is not None else "pending",
        evidence_pool="loaded" if pipeline_ready and evidence_count > 0 else "pending",
        evidence_count=evidence_count,
        device=str(DEVICE),
        embedding_model=EMBEDDING_MODEL_NAME,
    )
