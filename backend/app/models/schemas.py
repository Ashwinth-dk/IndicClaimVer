from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

# ============================================================================
# CLAIM VERIFICATION SCHEMAS
# ============================================================================

class ClaimRequest(BaseModel):
    claim: str = Field(..., min_length=1, description="The factual claim to verify in English, Tamil, Hindi, or Marathi")
    language: Optional[str] = Field(default=None, description="Optional expected language code ('en', 'ta', 'hi', 'mr')")

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
    language: str = "en"
    language_confidence: Optional[float] = None
    evidence: List[EvidenceItem]
    processing: ProcessingStatus
    model_name: str = "MuRIL (google/muril-base-cased fine-tuned)"
    model_version: Optional[str] = "baseline"
    metadata: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    model: str
    active_version: Optional[str] = "baseline"
    evidence_pool: str
    evidence_count: int
    training_examples_count: Optional[int] = 0
    rejected_count: Optional[int] = 0
    languages: Optional[Dict[str, int]] = None
    device: str
    embedding_model: str

# ============================================================================
# CRAWL & AUTOMATED PIPELINE SCHEMAS
# ============================================================================

class CrawlStartRequest(BaseModel):
    topic: str = Field(..., min_length=2, description="Topic or query to crawl")
    language: Optional[str] = Field(default="all", description="Language to crawl: 'en', 'ta', 'hi', 'mr', or 'all'")
    target_count: int = Field(default=100, ge=1, le=5000, description="Target training examples count")
    auto_train: bool = Field(default=True, description="Automatically trigger MuRIL training after crawl")
    epochs: int = Field(default=3, ge=1, le=20, description="Fine-tuning epochs")
    batch_size: int = Field(default=8, ge=1, le=64, description="Training batch size")
    learning_rate: float = Field(default=2e-5, description="Learning rate")
    source_types: Optional[List[str]] = Field(
        default=["government", "news", "fact_check", "legal", "research", "archive"],
        description="Source categories to search"
    )

class PipelineStartResponse(BaseModel):
    status: str
    job_id: str
    message: str

class PipelineStatusResponse(BaseModel):
    is_running: bool
    job_id: Optional[str] = None
    stage: str
    stage_details: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    language: Optional[str] = "all"
    language_statuses: Optional[Dict[str, str]] = None
    crawl_status: Optional[Dict[str, Any]] = None
    training_progress: Optional[Dict[str, Any]] = None
    crawl_result: Optional[Dict[str, Any]] = None
    training_result: Optional[Dict[str, Any]] = None
    trigger_status: Optional[Dict[str, Any]] = None

class TrainingTriggerRequest(BaseModel):
    epochs: int = Field(default=3, ge=1, le=20, description="Fine-tuning epochs")
    batch_size: int = Field(default=8, ge=1, le=64, description="Batch size")
    learning_rate: float = Field(default=2e-5, description="Learning rate")

class ThresholdUpdateRequest(BaseModel):
    threshold: int = Field(..., ge=1, le=10000, description="Minimum new examples required for automated retraining")

class AutoTrainToggleRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or pause automated training")

# ============================================================================
# DATASET & STORAGE SCHEMAS
# ============================================================================

class DatasetRecord(BaseModel):
    ID: str = Field(..., description="Unique ID: S1/000001")
    Text: str = Field(..., description="Claim statement")
    Evidence: str = Field(..., description="Evidence text")
    Label: Literal["SUPPORTS", "REFUTES"] = Field(..., description="Verification label")
    Language: Optional[str] = Field(default="en", description="Language code: en, ta, hi, mr")
    Source: Optional[str] = None
    SourceUrl: Optional[str] = None
    CreatedAt: Optional[str] = None
    Confidence: Optional[float] = None

class EvidenceRecord(BaseModel):
    ID: str = Field(..., description="Sequential ID: EV/100001")
    Evidence: str = Field(..., description="Clean evidence passage")

class RejectedRecord(BaseModel):
    ID: str = Field(..., description="Rejection ID: REJECTED/000001")
    Text: str = Field(..., description="Claim candidate text")
    Evidence: str = Field(..., description="Evidence candidate text")
    Reason: str = Field(..., description="Reason for rejection")
    Language: Optional[str] = None
    Confidence: Optional[float] = None
    ProposedLabel: Optional[str] = None
    Timestamp: Optional[str] = None
    Metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class SourceRecord(BaseModel):
    source_id: str
    source_name: str
    base_url: str
    language: Optional[str] = "en"
    source_type: Literal["government", "news", "fact_check", "legal", "research", "archive"]
    enabled: bool = True
    reliability_score: float = Field(default=0.9, ge=0.0, le=1.0)
    description: Optional[str] = None

class DatasetStatsResponse(BaseModel):
    total_count: int
    supports_count: int
    refutes_count: int
    balance_ratio: float
    evidence_count: int
    rejected_count: int
    sources_count: int
    languages: Optional[Dict[str, int]] = None

class ReviewActionRequest(BaseModel):
    action: Literal["approve", "reject", "edit_and_approve", "delete"]
    item_id: str
    label: Optional[Literal["SUPPORTS", "REFUTES"]] = None
    language: Optional[str] = None
    claim_text: Optional[str] = None
    evidence_text: Optional[str] = None
