import os
import re
import threading
import torch
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from backend.config import (
    SAVED_MODEL_DIR,
    CLASSIFIER_MODEL_NAME,
    LABEL2ID,
    ID2LABEL,
    MAX_SEQUENCE_LENGTH
)
from backend.data_pipeline import normalize_text

class VeracityModel:
    """
    Multi-Lingual Claim Veracity Prediction Model.
    Exclusively uses the fine-tuned XLM-RoBERTa cross-encoder saved model
    to classify (Claim, Evidence) pairs into SUPPORTS, REFUTES, or NOT ENOUGH INFO.
    """
    def __init__(self, model_dir: Path = SAVED_MODEL_DIR):
        self.model_dir = model_dir
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.is_custom_trained = False
        self._is_loading = False
        self._load_lock = threading.Lock()
        self.load_model()

    def start_background_load(self):
        """Starts model loading in a daemon thread if not already loaded."""
        if self.model is not None or self._is_loading:
            return
        t = threading.Thread(target=self._load_model_worker, daemon=True)
        t.start()

    def _load_model_worker(self):
        with self._load_lock:
            if self.model is not None:
                return
            self._is_loading = True
            try:
                self.load_model()
            finally:
                self._is_loading = False

    def load_model(self):
        """Loads saved fine-tuned model from saved_model directory."""
        if not self.model_dir.exists() or not (self.model_dir / "config.json").exists():
            raise FileNotFoundError(
                f"Saved model directory or config.json not found at: {self.model_dir}. "
                "Ensure fine-tuned model artifacts are present in the saved_model directory."
            )

        try:
            print(f"Loading saved fine-tuned model from {self.model_dir} on {self.device}...")
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_dir))
            self.model.to(self.device)
            self.model.eval()
            self.is_custom_trained = True
            print("Saved fine-tuned Veracity Model loaded successfully.")
        except Exception as e:
            self.model = None
            self.tokenizer = None
            self.is_custom_trained = False
            print(f"Error loading saved model: {e}")
            raise RuntimeError(f"Failed to load saved model from {self.model_dir}: {e}")

    def predict(self, claim: str, evidence: str) -> Dict[str, Any]:
        """
        Infers whether the given evidence SUPPORTS, REFUTES, or provides NOT ENOUGH INFO for the claim.
        Prediction is strictly performed using the saved fine-tuned model.
        """
        claim_clean = normalize_text(claim)
        evidence_clean = normalize_text(evidence)

        if not claim_clean:
            return {
                "veracity": "NOT ENOUGH INFO",
                "display_veracity": "INSUFFICIENT INFORMATION",
                "confidence": 0.0,
                "probabilities": {"SUPPORTS": 0.0, "REFUTES": 0.0, "NOT ENOUGH INFO": 1.0},
                "explanation": "No claim was provided for verification.",
                "model_source": "saved_model"
            }

        if not evidence_clean or len(evidence_clean) < 10:
            return {
                "veracity": "NOT ENOUGH INFO",
                "display_veracity": "INSUFFICIENT INFORMATION",
                "confidence": 0.0,
                "probabilities": {"SUPPORTS": 0.0, "REFUTES": 0.0, "NOT ENOUGH INFO": 1.0},
                "explanation": "No relevant evidence could be found to verify or refute this claim.",
                "model_source": "saved_model"
            }

        # Ensure saved model is loaded
        if self.model is None or self.tokenizer is None:
            self.load_model()

        if self.model is None or self.tokenizer is None:
            raise RuntimeError(f"Saved model is unavailable at {self.model_dir}. Prediction must only be through the saved model.")

        # Neural inference through saved model
        inputs = self.tokenizer(
            evidence_clean,
            claim_clean,
            max_length=MAX_SEQUENCE_LENGTH,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        pred_id = int(np.argmax(probs))
        confidence = float(probs[pred_id])

        # Dynamically retrieve label mapping from saved model config
        if hasattr(self.model, "config") and hasattr(self.model.config, "id2label") and self.model.config.id2label:
            id2lbl = self.model.config.id2label
            veracity = id2lbl.get(pred_id, id2lbl.get(str(pred_id), ID2LABEL.get(pred_id, "REFUTES")))
        else:
            veracity = ID2LABEL.get(pred_id, "REFUTES")

        # Dynamically build probability dictionary
        prob_dict = {"SUPPORTS": 0.0, "REFUTES": 0.0, "NOT ENOUGH INFO": 0.0}
        if hasattr(self.model, "config") and hasattr(self.model.config, "id2label") and self.model.config.id2label:
            for idx_val, p_val in enumerate(probs):
                lbl_name = self.model.config.id2label.get(idx_val, self.model.config.id2label.get(str(idx_val), str(idx_val)))
                prob_dict[lbl_name] = round(float(p_val), 4)
        else:
            for idx_val, p_val in enumerate(probs):
                lbl_name = ID2LABEL.get(idx_val, str(idx_val))
                prob_dict[lbl_name] = round(float(p_val), 4)

        display_map = {
            "SUPPORTS": "TRUE / SUPPORTED",
            "REFUTES": "FALSE / REFUTED",
            "NOT ENOUGH INFO": "UNVERIFIABLE / INSUFFICIENT INFO"
        }

        return {
            "veracity": veracity,
            "display_veracity": display_map.get(veracity, veracity),
            "confidence": round(confidence, 4),
            "probabilities": prob_dict,
            "explanation": self._generate_explanation(claim_clean, evidence_clean, veracity, confidence),
            "model_source": "saved_model"
        }

    def _generate_explanation(self, claim: str, evidence: str, veracity: str, confidence: float) -> str:
        pct = int(confidence * 100)
        if veracity == "SUPPORTS":
            return f"The saved fine-tuned model verified that the evidence directly confirms the claim ({pct}% confidence)."
        elif veracity == "REFUTES":
            return f"The saved fine-tuned model determined that the evidence contradicts or refutes the claim ({pct}% confidence)."
        else:
            return f"The saved fine-tuned model determined that the available evidence is insufficient to verify or refute this claim ({pct}% confidence)."

# Global singleton
_veracity_model_instance: Optional[VeracityModel] = None

def get_veracity_model() -> VeracityModel:
    global _veracity_model_instance
    if _veracity_model_instance is None:
        _veracity_model_instance = VeracityModel()
    return _veracity_model_instance

