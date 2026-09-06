import os
from pathlib import Path
import torch

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Model and Data paths
MODEL_PATH = Path(os.getenv("MODEL_PATH", BASE_DIR / "models" / "muril_claim_verification_model"))
LABEL_MAPPING_PATH = Path(os.getenv("LABEL_MAPPING_PATH", BASE_DIR / "models" / "label_mapping.json"))
EVIDENCE_POOL_PATH = Path(os.getenv("EVIDENCE_POOL_PATH", BASE_DIR / "data" / "evidence_pool.json"))
EMBEDDINGS_CACHE_PATH = Path(os.getenv("EMBEDDINGS_CACHE_PATH", BASE_DIR / "data" / "evidence_embeddings.npz"))

# Embedding and Retrieval Configuration
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
TOP_K = int(os.getenv("TOP_K", "5"))
INITIAL_RETRIEVAL_K = int(os.getenv("INITIAL_RETRIEVAL_K", "20"))
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "512"))
MIN_RELEVANCE_THRESHOLD = float(os.getenv("MIN_RELEVANCE_THRESHOLD", "0.22"))

# Device configuration (CUDA GPU if available, else CPU)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Fallback base model name if local config requires tokenizer base fallback
MURIL_BASE_NAME = "google/muril-base-cased"
