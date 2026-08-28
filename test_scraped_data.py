import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "dataset" / "crawled_dataset.json"
SAVED_MODEL_PATH = BASE_DIR / "saved_model"
FALLBACK_MODEL_PATH = BASE_DIR / "models" / "saved_classifier"

def load_data(file_path: Path) -> List[Dict[str, str]]:
    """Loads dataset and verifies 4-field structure."""
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Dataset must be a JSON array of objects, got {type(data)}")

    # Verify structure
    print(f"Loaded {len(data)} records from {file_path.name}")
    valid_records = []
    for idx, item in enumerate(data):
        claim = item.get("Text") or item.get("claim") or item.get("Claim") or ""
        evidence = item.get("Evidence") or item.get("evidence") or ""
        label = item.get("Label") or item.get("label") or "REFUTES"
        record_id = item.get("ID") or item.get("id") or f"ITEM_{idx+1}"

        # Standardize label
        label_str = label.strip().upper()
        if label_str in ["SUPPORTS", "SUPPORT", "TRUE", "CORRECT"]:
            canon_label = "SUPPORTS"
        else:
            canon_label = "REFUTES"

        if claim and evidence:
            valid_records.append({
                "ID": record_id,
                "Text": claim.strip(),
                "Evidence": evidence.strip(),
                "Label": canon_label
            })
    return valid_records

def get_model_path() -> Path:
    """Finds available saved model directory."""
    if SAVED_MODEL_PATH.exists() and (SAVED_MODEL_PATH / "config.json").exists():
        return SAVED_MODEL_PATH
    if FALLBACK_MODEL_PATH.exists() and (FALLBACK_MODEL_PATH / "config.json").exists():
        return FALLBACK_MODEL_PATH
    return SAVED_MODEL_PATH

def evaluate_model(
    dataset_path: Path = DEFAULT_DATASET,
    model_path: Path = None,
    max_samples: int = None,
    batch_size: int = 16
):
    """
    Loads the trained model and performs veracity evaluation on the dataset.
    """
    if model_path is None:
        model_path = get_model_path()

    print("=" * 80)
    print("VERICLAIM AI - MODEL EVALUATION & TESTING SUITE")
    print("=" * 80)
    print(f"Dataset Target:  {dataset_path}")
    print(f"Model Path:      {model_path}")
    
    # 1. Load Data
    records = load_data(dataset_path)
    if max_samples and max_samples < len(records):
        records = records[:max_samples]
        print(f"Evaluating subset of {len(records)} samples.")

    if not records:
        print("[!] No valid samples found to evaluate.")
        return

    # 2. Load Model & Tokenizer
    print("\n[*] Loading Transformer Model & Tokenizer...")
    t0 = time.time()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
    model.to(device)
    model.eval()
    print(f"[✓] Model successfully loaded on [{device}] in {time.time()-t0:.2f}s")
    print(f"[*] Model Label Mapping: {model.config.id2label}")

    id2label = model.config.id2label
    # Helper to resolve label string
    def resolve_label(idx):
        if idx in id2label:
            return id2label[idx]
        if str(idx) in id2label:
            return id2label[str(idx)]
        return "REFUTES" if idx == 0 else "SUPPORTS"

    # 3. Batch Inference
    print(f"\n[*] Running inference on {len(records)} samples...")
    results = []
    gold_labels = []
    pred_labels = []

    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        evidences = [b["Evidence"] for b in batch]
        claims = [b["Text"] for b in batch]

        inputs = tokenizer(
            evidences,
            claims,
            max_length=256,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1).cpu().numpy()

        for j, b in enumerate(batch):
            p = probs[j]
            pred_idx = int(np.argmax(p))
            predicted_label = resolve_label(pred_idx)
            confidence = float(p[pred_idx])

            gold = b["Label"]
            is_correct = (predicted_label == gold)

            gold_labels.append(gold)
            pred_labels.append(predicted_label)

            prob_map = {}
            for k_idx, k_prob in enumerate(p):
                prob_map[resolve_label(k_idx)] = round(float(k_prob), 4)

            results.append({
                "ID": b["ID"],
                "Text": b["Text"],
                "Evidence": b["Evidence"],
                "Gold_Label": gold,
                "Predicted_Label": predicted_label,
                "Confidence": round(confidence, 4),
                "Probabilities": prob_map,
                "Match": is_correct
            })

    # 4. Display Results Table
    print("\n" + "=" * 80)
    print("DETAILED SAMPLE-BY-SAMPLE VERACITY PREDICTIONS")
    print("=" * 80)
    
    for idx, r in enumerate(results):
        status_sym = "✓ MATCH   " if r["Match"] else "✗ MISMATCH"
        print(f"\n[{idx+1:03d}] ID: {r['ID']} | Result: [{status_sym}]")
        print(f"      Claim:     {r['Text'][:95]}..." if len(r['Text']) > 95 else f"      Claim:     {r['Text']}")
        print(f"      Evidence:  {r['Evidence'][:95]}..." if len(r['Evidence']) > 95 else f"      Evidence:  {r['Evidence']}")
        print(f"      Gold:      {r['Gold_Label']:<10} | Predicted: {r['Predicted_Label']:<10} | Confidence: {r['Confidence']*100:.2f}%")
        print(f"      Probabilities: {r['Probabilities']}")

    # 5. Compute Quantitative Metrics
    print("\n" + "=" * 80)
    print("OVERALL PERFORMANCE EVALUATION SUMMARY")
    print("=" * 80)

    acc = accuracy_score(gold_labels, pred_labels)
    prec_macro, rec_macro, f1_macro, _ = precision_recall_fscore_support(
        gold_labels, pred_labels, average="macro", zero_division=0
    )
    prec_weighted, rec_weighted, f1_weighted, _ = precision_recall_fscore_support(
        gold_labels, pred_labels, average="weighted", zero_division=0
    )

    correct_cnt = sum(1 for r in results if r["Match"])
    total_cnt = len(results)

    print(f"\n  Total Evaluated Samples:   {total_cnt}")
    print(f"  Correct Predictions:       {correct_cnt} / {total_cnt}")
    print(f"  Overall Accuracy:          {acc*100:.2f}%")
    print(f"  Macro Precision:           {prec_macro*100:.2f}%")
    print(f"  Macro Recall:              {rec_macro*100:.2f}%")
    print(f"  Macro F1-Score:            {f1_macro*100:.2f}%")
    print(f"  Weighted F1-Score:         {f1_weighted*100:.2f}%\n")

    print("Detailed Classification Report:")
    print(classification_report(gold_labels, pred_labels, zero_division=0, digits=4))

    labels_unique = sorted(list(set(gold_labels + pred_labels)))
    cm = confusion_matrix(gold_labels, pred_labels, labels=labels_unique)
    print("Confusion Matrix:")
    print(f"  Labels order: {labels_unique}")
    for i_row, row_label in enumerate(labels_unique):
        print(f"  Actual {row_label:<10}: {cm[i_row]}")

    # 6. Save JSON Evaluation Report
    report_output_path = BASE_DIR / "dataset" / "test_evaluation_report.json"
    report_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "dataset_file": str(dataset_path),
        "total_samples": total_cnt,
        "correct_predictions": correct_cnt,
        "metrics": {
            "accuracy": round(acc, 4),
            "macro_precision": round(prec_macro, 4),
            "macro_recall": round(rec_macro, 4),
            "macro_f1": round(f1_macro, 4),
            "weighted_f1": round(f1_weighted, 4)
        },
        "confusion_matrix": {
            "labels": labels_unique,
            "matrix": cm.tolist()
        },
        "predictions": results
    }

    with open(report_output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=4, ensure_ascii=False)

    print(f"\n[✓] Full evaluation report saved to: {report_output_path}")
    print("=" * 80)
    return report_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test and Evaluate Trained Veracity Model on Dataset")
    parser.add_argument("--data", type=str, default=str(DEFAULT_DATASET), help="Path to evaluation JSON dataset")
    parser.add_argument("--model", type=str, default=None, help="Path to saved model directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of samples to test")
    parser.add_argument("--batch-size", type=int, default=16, help="Inference batch size")

    args = parser.parse_args()
    evaluate_model(
        dataset_path=Path(args.data),
        model_path=Path(args.model) if args.model else None,
        max_samples=args.limit,
        batch_size=args.batch_size
    )
