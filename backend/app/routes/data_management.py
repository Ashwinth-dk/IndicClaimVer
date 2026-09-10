import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Response, Depends

from app.storage.dataset_manager import DatasetManager
from app.storage.evidence_manager import EvidenceManager
from app.storage.review_manager import ReviewManager
from app.storage.source_manager import SourceManager
from app.models.schemas import DatasetStatsResponse, ReviewActionRequest
from app.auth import verify_admin_access

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["Data Management"],
    dependencies=[Depends(verify_admin_access)]
)

dataset_mgr = DatasetManager()
evidence_mgr = EvidenceManager()
review_mgr = ReviewManager()
source_mgr = SourceManager()

# ============================================================================
# OVERALL STATS
# ============================================================================

@router.get("/stats", response_model=DatasetStatsResponse)
async def get_system_stats():
    ds_stats = dataset_mgr.get_stats()
    ev_count = evidence_mgr.get_count()
    rev_count = review_mgr.get_count()
    sources = source_mgr.load_all()

    return DatasetStatsResponse(
        total_count=ds_stats["total_count"],
        supports_count=ds_stats["supports_count"],
        refutes_count=ds_stats["refutes_count"],
        balance_ratio=ds_stats["balance_ratio"],
        evidence_count=ev_count,
        rejected_count=rev_count,
        sources_count=len(sources),
        languages=ds_stats.get("languages", {})
    )

# ============================================================================
# DATASET (train_subtask1.json)
# ============================================================================

@router.get("/dataset")
async def get_dataset_items(
    search: Optional[str] = Query(None),
    label: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("ID"),
    sort_order: str = Query("desc"),
):
    items, total = dataset_mgr.query_items(
        search=search, label=label, language=language, offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order
    )
    return {"items": items, "total": total, "offset": offset, "limit": limit}

@router.get("/dataset/export")
async def export_dataset(format: str = Query("json"), label: Optional[str] = Query(None), language: Optional[str] = Query(None)):
    data = dataset_mgr.export_data(format_type=format, label_filter=label, language_filter=language)
    media_type = "text/csv" if format == "csv" else "application/json"
    return Response(content=data, media_type=media_type)

# ============================================================================
# EVIDENCE POOL (evidence_pool.json)
# ============================================================================

@router.get("/evidence")
async def get_evidence_items(
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("ID"),
    sort_order: str = Query("desc"),
):
    items, total = evidence_mgr.query_items(
        search=search, offset=offset, limit=limit, sort_by=sort_by, sort_order=sort_order
    )
    return {"items": items, "total": total, "offset": offset, "limit": limit}

@router.get("/evidence/export")
async def export_evidence(format: str = Query("json")):
    data = evidence_mgr.export_data(format_type=format)
    media_type = "text/csv" if format == "csv" else "application/json"
    return Response(content=data, media_type=media_type)

# ============================================================================
# REVIEW QUEUE (rejected_examples.json)
# ============================================================================

@router.get("/review")
async def get_review_items(
    search: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = review_mgr.query_items(search=search, offset=offset, limit=limit)
    return {"items": items, "total": total, "offset": offset, "limit": limit}

@router.post("/review/action")
async def handle_review_action(request: ReviewActionRequest):
    if request.action == "approve":
        item = review_mgr.pop_item(request.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        label = request.label or item.get("ProposedLabel") or "SUPPORTS"
        added = dataset_mgr.add_item(
            text=item.get("Text", ""),
            evidence=item.get("Evidence", ""),
            label=label,
        )
        return {"status": "success", "action": "approved", "item": added}

    elif request.action == "edit_and_approve":
        item = review_mgr.pop_item(request.item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        claim_text = request.claim_text or item.get("Text", "")
        evidence_text = request.evidence_text or item.get("Evidence", "")
        label = request.label or "SUPPORTS"
        added = dataset_mgr.add_item(
            text=claim_text,
            evidence=evidence_text,
            label=label,
        )
        return {"status": "success", "action": "edited_and_approved", "item": added}

    elif request.action == "delete":
        deleted = review_mgr.delete_item(request.item_id)
        return {"status": "success", "action": "deleted", "deleted": deleted}

    raise HTTPException(status_code=400, detail=f"Unsupported action: {request.action}")

# ============================================================================
# SOURCE REGISTRY (source_registry.json)
# ============================================================================

@router.get("/sources")
async def get_sources():
    sources = source_mgr.load_all()
    return {"sources": sources, "total": len(sources)}

@router.post("/sources/{source_id}/toggle")
async def toggle_source(source_id: str, enabled: bool = Query(...)):
    res = source_mgr.toggle_source(source_id, enabled)
    if not res:
        raise HTTPException(status_code=404, detail="Source not found")
    return {"status": "success", "source": res}


# ============================================================================
# MODELS REGISTRY
# ============================================================================

@router.get("/models")
async def get_all_models():
    """List active and archived MuRIL model checkpoints."""
    from app.services.training_service import TrainingService
    ts = TrainingService()
    models = ts.list_all_models()
    return {"models": models, "total": len(models)}
