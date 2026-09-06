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
from app.routes.verification import router as verification_router, set_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("IndicClaimVer")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler: Loads AI models and computes/loads
    vector index once when FastAPI server starts up.
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

    # 3. Initialize and load fine-tuned MuRIL model
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

    logger.info("==========================================")
    logger.info("IndicClaimVer Pipeline Ready for Requests!")
    logger.info("==========================================")
    
    yield
    
    logger.info("Shutting down IndicClaimVer service...")

app = FastAPI(
    title="IndicClaimVer API",
    description="AI-Powered Indic Claim Verification with Fine-Tuned MuRIL and Semantic Evidence Retrieval",
    version="1.0.0",
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

# Include verification routes
app.include_router(verification_router)

@app.get("/")
async def root():
    return {
        "service": "IndicClaimVer API",
        "description": "AI-Powered Evidence Retrieval and Claim Verification",
        "version": "1.0.0",
        "endpoints": {
            "verify": "POST /api/verify",
            "health": "GET /api/health",
            "docs": "/docs",
        },
    }
