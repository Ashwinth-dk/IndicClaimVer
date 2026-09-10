import os
from pathlib import Path
import torch

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Model and Data directories
MODELS_DIR = Path(os.getenv("MODELS_DIR", BASE_DIR / "models"))
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Specific file paths
MODEL_PATH = Path(os.getenv("MODEL_PATH", MODELS_DIR / "muril_claim_verification_model"))
MODEL_METADATA_PATH = Path(os.getenv("MODEL_METADATA_PATH", MODELS_DIR / "model_metadata.json"))
LABEL_MAPPING_PATH = Path(os.getenv("LABEL_MAPPING_PATH", MODELS_DIR / "label_mapping.json"))

TRAIN_DATASET_PATH = Path(os.getenv("TRAIN_DATASET_PATH", DATA_DIR / "train_subtask1.json"))
EVIDENCE_POOL_PATH = Path(os.getenv("EVIDENCE_POOL_PATH", DATA_DIR / "evidence_pool.json"))
REJECTED_EXAMPLES_PATH = Path(os.getenv("REJECTED_EXAMPLES_PATH", DATA_DIR / "rejected_examples.json"))
SOURCE_REGISTRY_PATH = Path(os.getenv("SOURCE_REGISTRY_PATH", DATA_DIR / "source_registry.json"))
EMBEDDINGS_CACHE_PATH = Path(os.getenv("EMBEDDINGS_CACHE_PATH", DATA_DIR / "evidence_embeddings.npz"))

# Embedding and Retrieval Configuration
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
TOP_K = int(os.getenv("TOP_K", "5"))
INITIAL_RETRIEVAL_K = int(os.getenv("INITIAL_RETRIEVAL_K", "20"))
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "512"))
MIN_RELEVANCE_THRESHOLD = float(os.getenv("MIN_RELEVANCE_THRESHOLD", "0.22"))

# Crawler Configuration
CRAWL_MAX_CONCURRENT_REQUESTS = int(os.getenv("CRAWL_MAX_CONCURRENT_REQUESTS", "20"))
CRAWL_TIMEOUT = float(os.getenv("CRAWL_TIMEOUT", "4.5"))
CRAWL_BATCH_SIZE = int(os.getenv("CRAWL_BATCH_SIZE", "5"))

# Training Configuration & Automation Triggers
MIN_NEW_EXAMPLES_FOR_RETRAIN = int(os.getenv("MIN_NEW_EXAMPLES_FOR_RETRAIN", "100"))
MIN_TRAINING_EXAMPLES = int(os.getenv("MIN_TRAINING_EXAMPLES", "50"))
MIN_PER_LABEL = int(os.getenv("MIN_PER_LABEL", "15"))
MIN_MODEL_ACCURACY = float(os.getenv("MIN_MODEL_ACCURACY", "0.50"))
MIN_MODEL_F1 = float(os.getenv("MIN_MODEL_F1", "0.50"))
MAX_ALLOWED_LABEL_IMBALANCE = float(os.getenv("MAX_ALLOWED_LABEL_IMBALANCE", "0.80"))

DEFAULT_EPOCHS = int(os.getenv("DEFAULT_EPOCHS", "3"))
DEFAULT_BATCH_SIZE = int(os.getenv("DEFAULT_BATCH_SIZE", "8"))
DEFAULT_LEARNING_RATE = float(os.getenv("DEFAULT_LEARNING_RATE", "2e-5"))

# Device configuration (CUDA GPU if available, else CPU)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Fallback base model name if local config requires tokenizer base fallback
MURIL_BASE_NAME = "google/muril-base-cased"

# Authentication
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "indicclaim-dev-admin-secure-key-2026")


