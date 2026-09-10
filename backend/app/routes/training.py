import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Body, Path

from app.models.schemas import (
    TrainingTriggerRequest,
    ThresholdUpdateRequest,
    AutoTrainToggleRequest
)
from app.auth import verify_admin_access
from app.routes.crawl import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Training & Model Management"],
    dependencies=[Depends(verify_admin_access)]
)

@router.get("/training/status")
async def get_training_trigger_status(orchestrator = Depends(get_orchestrator)):
    """Returns the automated retraining trigger counter, threshold, lock, and quality metrics."""
    return orchestrator.trainer.get_trigger_status()

@router.post("/training/trigger")
async def manual_train_trigger(
    request: Optional[TrainingTriggerRequest] = None,
    orchestrator = Depends(get_orchestrator)
):
    """Developer/admin manual override to train MuRIL model immediately."""
    epochs = request.epochs if request else 3
    batch_size = request.batch_size if request else 8
    lr = request.learning_rate if request else 2e-5
    
    result = orchestrator.trigger_training_only(
        epochs=epochs,
        batch_size=batch_size,
        learning_rate=lr
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=409, detail=result.get("message"))
    return result

@router.post("/training/pause")
async def pause_auto_training(orchestrator = Depends(get_orchestrator)):
    """Pause automatic retraining when threshold is reached."""
    enabled = orchestrator.trainer.set_auto_train_enabled(False)
    return {"status": "success", "auto_train_enabled": enabled, "message": "Automatic training paused."}

@router.post("/training/resume")
async def resume_auto_training(orchestrator = Depends(get_orchestrator)):
    """Resume automatic retraining."""
    enabled = orchestrator.trainer.set_auto_train_enabled(True)
    return {"status": "success", "auto_train_enabled": enabled, "message": "Automatic training resumed."}

@router.post("/training/threshold")
async def update_retrain_threshold(
    request: ThresholdUpdateRequest,
    orchestrator = Depends(get_orchestrator)
):
    """Update the number of new valid records required before automated fine-tuning triggers."""
    new_threshold = orchestrator.trainer.set_retrain_threshold(request.threshold)
    return {"status": "success", "threshold": new_threshold}

@router.post("/models/{version}/activate")
async def activate_model(
    version: str = Path(..., description="Model version (e.g. 'v1', 'v2', 'baseline')"),
    orchestrator = Depends(get_orchestrator)
):
    """Promote a specific model version to active and hot-reload in memory."""
    try:
        model = orchestrator.trainer.activate_model_version(version)
        if orchestrator.reload_model_callback:
            orchestrator.reload_model_callback(model["model_path"])
        return {"status": "success", "activated_version": version, "model": model}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/models/{version}/rollback")
async def rollback_model(
    version: str = Path(..., description="Model version to rollback to"),
    orchestrator = Depends(get_orchestrator)
):
    """Rollback active model to a previous version and hot-reload in memory."""
    try:
        model = orchestrator.trainer.rollback_to_version(version)
        if orchestrator.reload_model_callback:
            orchestrator.reload_model_callback(model["model_path"])
        return {"status": "success", "rollback_version": version, "model": model}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
