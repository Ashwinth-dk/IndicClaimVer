import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "dataset"
SAVED_MODEL_DIR = BASE_DIR / "saved_model"
CRAWLED_DATA_PATH = DATASET_DIR / "crawled_dataset.json"
TRAIN_DATA_PATH = DATASET_DIR / "train_subtask1.json"
DEV_DATA_PATH = DATASET_DIR / "dev_subtask1.json"
DEV_SUBTASK2_PATH = DATASET_DIR / "dev_subtask2.json"
EVIDENCE_POOL_PATH = DATASET_DIR / "evidence_pool.json"
INDEX_CACHE_PATH = BASE_DIR / "retriever_cache"

# Ensure directories exist
SAVED_MODEL_DIR.mkdir(parents=True, exist_ok=True)
INDEX_CACHE_PATH.mkdir(parents=True, exist_ok=True)

# Model Settings
# Default to high-performance multilingual model
CLASSIFIER_MODEL_NAME = "xlm-roberta-base"
RETRIEVER_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SENTENCE_SELECTOR_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Classification Hyperparameters
MAX_SEQUENCE_LENGTH = 256
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
NUM_EPOCHS = 5
WEIGHT_DECAY = 0.01

# Labels
LABEL2ID = {
    "SUPPORTS": 0,
    "REFUTES": 1,
    "NOT ENOUGH INFO": 2
}

ID2LABEL = {
    0: "SUPPORTS",
    1: "REFUTES",
    2: "NOT ENOUGH INFO"
}

# Thresholds
RETRIEVAL_TOP_K = 5
SENTENCE_TOP_K = 3
CONFIDENCE_THRESHOLD = 0.55

# Web Scraper User-Agent
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Server Settings
API_HOST = "127.0.0.1"
API_PORT = 8000
