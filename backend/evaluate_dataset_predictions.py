import json
import logging
from pathlib import Path
from typing import Dict, Any, List
import torch
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from app.services.claim_verifier import ClaimVerifier
from app.config import TRAIN_DATASET_PATH, MODEL_METADATA_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_model_on_dataset(max_samples: int = 200) -> Dict[str, Any]:
    print("=" * 60)
    print("EXACT DATASET CORRECTNESS & EVALUATION REPORT")
    print("=" * 60)

    # 1. Load active metadata
    active_version = "baseline"
    if MODEL_METADATA_PATH.exists():
        with open(MODEL_METADATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
            active_version = meta.get("active_version", "baseline")

    print(f"Active Model Version: {active_version}")

    # 2. Load verifier
    verifier = ClaimVerifier()
    verifier.load_model()

    # 3. Load dataset
    with open(TRAIN_DATASET_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # Take a balanced slice of dataset items with claim, evidence, and label
    valid_items = [
        item for item in raw_data
        if item.get("Text") and item.get("Evidence") and item.get("Label") in ["SUPPORTS", "REFUTES"]
    ]

    supports_items = [item for item in valid_items if item["Label"] == "SUPPORTS"]
    refutes_items = [item for item in valid_items if item["Label"] == "REFUTES"]

    half = max_samples // 2
    eval_items = supports_items[:half] + refutes_items[:half]
    print(f"Evaluating {len(eval_items)} items ({len(supports_items[:half])} SUPPORTS, {len(refutes_items[:half])} REFUTES)...")

    y_true = []
    y_pred = []
    mismatches = []

    for i, item in enumerate(eval_items):
        claim = item["Text"]
        evidence = item["Evidence"]
        expected = item["Label"]

        result = verifier.verify_pair(claim, evidence)
        predicted = result["prediction"]
        confidence = result["confidence"]

        y_true.append(expected)
        y_pred.append(predicted)

        if expected != predicted:
            mismatches.append({
                "id": item.get("ID", f"eval_{i}"),
                "claim": claim[:100],
                "expected": expected,
                "predicted": predicted,
                "confidence": confidence,
                "model_version": active_version
            })

    # Metrics
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    p_sup, r_sup, f1_sup, _ = precision_recall_fscore_support(
        [1 if y == "SUPPORTS" else 0 for y in y_true],
        [1 if y == "SUPPORTS" else 0 for y in y_pred],
        average="binary",
        zero_division=0
    )
    p_ref, r_ref, f1_ref, _ = precision_recall_fscore_support(
        [1 if y == "REFUTES" else 0 for y in y_true],
        [1 if y == "REFUTES" else 0 for y in y_pred],
        average="binary",
        zero_division=0
    )

    labels = ["REFUTES", "SUPPORTS"]
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    print("\n------------------------------------------------------------")
    print("EVALUATION RESULTS:")
    print(f"Total evaluated:      {len(eval_items)}")
    print(f"Overall Accuracy:     {acc:.4f} ({acc*100:.2f}%)")
    print(f"Weighted Precision:   {p:.4f}")
    print(f"Weighted Recall:      {r:.4f}")
    print(f"Weighted F1:          {f1:.4f}")
    print("\nPER-LABEL BREAKDOWN:")
    print(f"  SUPPORTS -> Precision: {p_sup:.4f}, Recall: {r_sup:.4f}, F1: {f1_sup:.4f}")
    print(f"  REFUTES  -> Precision: {p_ref:.4f}, Recall: {r_ref:.4f}, F1: {f1_ref:.4f}")
    print("\nCONFUSION MATRIX (Rows: Actual, Cols: Predicted):")
    print(f"              Pred REFUTES   Pred SUPPORTS")
    print(f"  Act REFUTES      {cm[0][0]:<14} {cm[0][1]:<14}")
    print(f"  Act SUPPORTS     {cm[1][0]:<14} {cm[1][1]:<14}")
    print("------------------------------------------------------------")

    if mismatches:
        print(f"\nMismatches ({len(mismatches)} total, showing up to 5):")
        for m in mismatches[:5]:
            print(f"  [ID {m['id']}] Expected: {m['expected']} | Predicted: {m['predicted']} (Conf: {m['confidence']})")
            print(f"    Claim: {m['claim']}...")
    else:
        print("\nZero mismatches! 100% exact match on evaluated items.")

    return {
        "total_evaluated": len(eval_items),
        "accuracy": acc,
        "precision": p,
        "recall": r,
        "f1": f1,
        "confusion_matrix": cm.tolist(),
        "per_label": {
            "SUPPORTS": {"precision": p_sup, "recall": r_sup, "f1": f1_sup},
            "REFUTES": {"precision": p_ref, "recall": r_ref, "f1": f1_ref}
        },
        "mismatches_count": len(mismatches)
    }

if __name__ == "__main__":
    evaluate_model_on_dataset(max_samples=20)
