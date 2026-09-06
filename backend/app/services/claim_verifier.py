import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from app.config import (
    MODEL_PATH,
    LABEL_MAPPING_PATH,
    MAX_LENGTH,
    DEVICE,
    MURIL_BASE_NAME,
)

logger = logging.getLogger(__name__)

class ClaimVerifier:
    """
    MuRIL-based Claim Verification sequence classifier.
    Classifies (claim, evidence) pairs as SUPPORTS or REFUTES.
    """

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
        label_mapping_path: Path = LABEL_MAPPING_PATH,
        max_length: int = MAX_LENGTH,
        device: str = DEVICE,
    ):
        self.model_path = Path(model_path)
        self.label_mapping_path = Path(label_mapping_path)
        self.max_length = max_length
        self.device = torch.device(device)

        self.tokenizer = None
        self.model = None
        
        # Default fallback mapping: {"REFUTES": 0, "SUPPORTS": 1}
        self.label2id = {"REFUTES": 0, "SUPPORTS": 1}
        self.id2label = {0: "REFUTES", 1: "SUPPORTS"}
        self._load_label_mapping()

    def _load_label_mapping(self):
        """Loads label mapping from JSON if available."""
        if self.label_mapping_path.exists():
            try:
                with open(self.label_mapping_path, "r", encoding="utf-8") as f:
                    mapping = json.load(f)
                    self.label2id = mapping
                    self.id2label = {int(v): k for k, v in mapping.items()}
                logger.info(f"Loaded label mapping: {self.id2label}")
            except Exception as e:
                logger.warning(f"Failed to load label mapping from {self.label_mapping_path}: {e}")

    def load_model(self):
        """Loads the fine-tuned MuRIL model and tokenizer once into memory."""
        logger.info(f"Loading MuRIL claim verification model from {self.model_path}...")
        
        # Load Tokenizer
        try:
            from transformers import BertTokenizerFast
            self.tokenizer = BertTokenizerFast.from_pretrained(str(self.model_path), use_fast=True)
            logger.info("BertTokenizerFast loaded directly from local model directory.")
        except Exception as e:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path), use_fast=True)
                logger.info("AutoTokenizer loaded from local model directory.")
            except Exception as e2:
                logger.warning(f"Could not load local tokenizer ({e2}), loading '{MURIL_BASE_NAME}'...")
                self.tokenizer = AutoTokenizer.from_pretrained(MURIL_BASE_NAME, use_fast=True)

        # Load Sequence Classification Model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            str(self.model_path),
            num_labels=len(self.id2label),
        )
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"MuRIL model loaded successfully on device: {self.device}")

    def verify_pair(self, claim: str, evidence: str) -> Dict[str, Any]:
        """
        Verifies a single (claim, evidence) pair.
        Returns predicted label, confidence, and full probability distribution.
        """
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("ClaimVerifier model not loaded. Call load_model() first.")

        # Sequence pair tokenization: [CLS] claim [SEP] evidence [SEP]
        inputs = self.tokenizer(
            claim,
            evidence,
            truncation=True,
            max_length=self.max_length,
            padding=True,
            return_tensors="pt",
        )
        
        # Move tensors to target device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits  # shape: [1, num_labels]
            probs = F.softmax(logits, dim=-1)[0]  # shape: [num_labels]

        supports_id = self.label2id.get("SUPPORTS", 1)
        refutes_id = self.label2id.get("REFUTES", 0)

        supports_prob = float(probs[supports_id].cpu().item())
        refutes_prob = float(probs[refutes_id].cpu().item())

        predicted_idx = int(torch.argmax(probs).cpu().item())
        predicted_label = self.id2label.get(predicted_idx, "REFUTES")
        confidence = float(probs[predicted_idx].cpu().item())

        return {
            "prediction": predicted_label,
            "confidence": round(confidence, 4),
            "supports_prob": round(supports_prob, 4),
            "refutes_prob": round(refutes_prob, 4),
        }
