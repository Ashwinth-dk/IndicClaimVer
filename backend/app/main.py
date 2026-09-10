import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    MODEL_PATH,
    LABEL_MAPPING_PATH,
    EVIDENCE_POOL_PATH,
    EMBEDDINGS_CACHE_PATH,
    EMBEDDING_MODEL_NAME,
    DEVICE,
    TOP_K,
)
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.claim_verifier import ClaimVerifier
from app.services.pipeline import VerificationPipeline
from app.services.pipeline_orchestrator import PipelineOrchestrator
from app.routes.verification import router as verification_router, set_pipeline
from app.routes.crawl import router as crawl_router, set_orchestrator
from app.routes.data_management import router as data_router
from app.routes.training import router as training_router
from app.auth import router as auth_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("IndicClaimVer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler: Loads AI models and computes/loads
    vector index once when FastAPI server starts up. Also initializes
    the end-to-end automated crawl and training orchestrator.
    """
    logger.info("==========================================")
    logger.info("Initializing IndicClaimVer Pipeline...")
    logger.info(f"Target Device: {DEVICE}")
    logger.info("==========================================")

    # 1. Initialize and build Evidence Retriever
    retriever = EvidenceRetriever(
        pool_path=EVIDENCE_POOL_PATH,
        cache_path=EMBEDDINGS_CACHE_PATH,
        model_name=EMBEDDING_MODEL_NAME,
        device=DEVICE,
    )
    retriever.build_index()

    # 2. Initialize Evidence Ranker
    ranker = EvidenceRanker(top_k=TOP_K)

    # 3. Initialize and load fine-tuned MuRIL model (active version)
    verifier = ClaimVerifier(
        model_path=MODEL_PATH,
        label_mapping_path=LABEL_MAPPING_PATH,
        device=DEVICE,
    )
    verifier.load_model()

    # 4. Assemble Verification Pipeline
    pipeline = VerificationPipeline(
        retriever=retriever,
        ranker=ranker,
        verifier=verifier,
    )
    set_pipeline(pipeline)

    # 5. Define hot-reload callbacks for automated training pipeline
    def handle_rebuild_index():
        logger.info("[HOT-RELOAD] Rebuilding evidence index after crawl...")
        retriever.load_evidence()
        retriever.build_index(force_recompute=True)
        logger.info("[HOT-RELOAD] Evidence index updated successfully.")

    def handle_reload_model(new_model_path: str):
        logger.info(f"[HOT-RELOAD] Reloading active MuRIL model from {new_model_path}...")
        verifier.reload_active_model(new_model_path)
        logger.info("[HOT-RELOAD] MuRIL model reloaded successfully.")

    # 6. Initialize Pipeline Orchestrator with hot-reload callbacks
    orchestrator = PipelineOrchestrator(
        rebuild_index_callback=handle_rebuild_index,
        reload_model_callback=handle_reload_model,
    )
    set_orchestrator(orchestrator)

    logger.info("==========================================")
    logger.info("IndicClaim End-to-End System Ready!")
    logger.info("==========================================")
    
    yield
    
    logger.info("Shutting down IndicClaimVer service...")

app = FastAPI(
    title="IndicClaim Integrated API",
    description="Unified Fact Verification System & Automated Crawler-to-MuRIL Training Pipeline",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all route handlers
app.include_router(auth_router)
app.include_router(verification_router)
app.include_router(crawl_router)
app.include_router(data_router)
app.include_router(training_router)

@app.get("/")
async def root():
    return {
        "service": "IndicClaim Integrated API",
        "version": "2.0.0",
        "description": "Unified Automated Crawl, Quality Validation, MuRIL Training, and Fact Verification",
        "endpoints": {
            "verify_claim": "POST /api/verify",
            "health": "GET /api/health",
            "start_crawl": "POST /api/crawl/start",
            "crawl_status": "GET /api/crawl/status",
            "stop_crawl": "POST /api/crawl/stop",
            "pipeline_history": "GET /api/crawl/history",
            "active_model": "GET /api/crawl/active-model",
            "dataset_stats": "GET /api/stats",
            "dataset_items": "GET /api/dataset",
            "evidence_items": "GET /api/evidence",
            "review_queue": "GET /api/review",
            "sources": "GET /api/sources",
            "docs": "/docs",
        },
    }

