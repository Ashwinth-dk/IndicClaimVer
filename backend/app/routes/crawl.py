import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query

from app.models.schemas import (
    CrawlStartRequest,
    PipelineStartResponse,
    PipelineStatusResponse,
)
from app.auth import verify_admin_access

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/crawl",
    tags=["Automated Pipeline"],
    dependencies=[Depends(verify_admin_access)]
)

# Global orchestrator instance initialized on app lifespan
_orchestrator = None

def get_orchestrator():
    if _orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Pipeline orchestrator is not initialized.",
        )
    return _orchestrator

def set_orchestrator(orchestrator):
    global _orchestrator
    _orchestrator = orchestrator

@router.post("/start", response_model=PipelineStartResponse)
async def start_crawl_pipeline(
    request: CrawlStartRequest,
    orchestrator = Depends(get_orchestrator),
):
    """
    Triggers the end-to-end automated pipeline:
    1. Crawls web sources for the requested topic
    2. Extracts and normalizes factual claims + evidence
    3. Strictly validates and deduplicates records
    4. Updates evidence_pool.json and train_subtask1.json
    5. Fine-tunes MuRIL model when sufficient data exists
    6. Evaluates and activates new model version
    7. Hot-reloads active model into verification pipeline
    """
    if not request.topic or not request.topic.strip():
        raise HTTPException(status_code=400, detail="Topic cannot be empty.")

    result = orchestrator.start_pipeline(
        topic=request.topic.strip(),
        language=request.language or "all",
        target_count=request.target_count,
        auto_train=request.auto_train,
        epochs=request.epochs,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate,
    )

    if result.get("status") == "error":
        raise HTTPException(status_code=409, detail=result.get("message", "Pipeline already running"))

    return PipelineStartResponse(
        status="STARTED",
        job_id=result.get("job_id", ""),
        message=result.get("message", f"Pipeline started for topic '{request.topic}' ({request.language or 'all'})"),
    )

@router.get("/status", response_model=PipelineStatusResponse)
async def get_current_pipeline_status(
    orchestrator = Depends(get_orchestrator),
):
    """Returns the live status, current stage, progress, logs, and telemetry."""
    status = orchestrator.get_status()
    return PipelineStatusResponse(**status)

@router.get("/status/{job_id}", response_model=PipelineStatusResponse)
async def get_job_status(
    job_id: str,
    orchestrator = Depends(get_orchestrator),
):
    """Returns pipeline status for a specific job ID."""
    status = orchestrator.get_status()
    return PipelineStatusResponse(**status)

@router.post("/stop")
async def stop_pipeline_endpoint(
    orchestrator = Depends(get_orchestrator),
):
    """Stops the running pipeline."""
    return orchestrator.stop_pipeline()

@router.get("/history")
async def get_pipeline_history(
    orchestrator = Depends(get_orchestrator),
):
    """Returns past pipeline execution runs with results."""
    return orchestrator.get_history()

@router.get("/active-model")
async def get_active_model_metadata(
    orchestrator = Depends(get_orchestrator),
):
    """Returns metadata about the currently active MuRIL model."""
    return orchestrator.trainer.get_active_model_info()
