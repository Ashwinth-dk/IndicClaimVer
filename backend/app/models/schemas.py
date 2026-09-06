from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ClaimRequest(BaseModel):
    claim: str = Field(..., min_length=1, description="The factual claim to verify")

class EvidenceItem(BaseModel):
    rank: int = Field(..., description="Rank in retrieved results (1-indexed)")
    id: str = Field(..., description="Evidence identifier")
    text: str = Field(..., description="Evidence text passage")
    retrieval_score: float = Field(..., description="Cosine similarity score from retrieval (0.0 - 1.0)")
    prediction: str = Field(..., description="Per-evidence MuRIL prediction (SUPPORTS or REFUTES)")
    confidence: float = Field(..., description="MuRIL model confidence for this evidence (0.0 - 1.0)")

class ProcessingStatus(BaseModel):
    claim_analysis: str = "completed"
    evidence_retrieval: str = "completed"
    evidence_ranking: str = "completed"
    verification: str = "completed"

class VerificationResponse(BaseModel):
    claim: str
    verdict: str  # "SUPPORTS", "REFUTES", or "INSUFFICIENT_EVIDENCE"
    confidence: float
    supports_score: float
    refutes_score: float
    summary: Optional[str] = None
    evidence: List[EvidenceItem]
    processing: ProcessingStatus
    model_name: str = "MuRIL (google/muril-base-cased fine-tuned)"
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    model: str
    evidence_pool: str
    evidence_count: int
    device: str
    embedding_model: str
