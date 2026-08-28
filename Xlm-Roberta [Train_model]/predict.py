import sys
import io
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parent.parent
model_path = BASE_DIR / "saved_model"

if not model_path.exists():
    raise FileNotFoundError(f"Saved model directory not found at {model_path}")

print(f"Loading model from {model_path}...")
tokenizer = AutoTokenizer.from_pretrained(str(model_path))
model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
model.eval()

# Sample Bengali Claim and Evidence
text = "প্রতি ঘণ্টায় চাই হোম কোয়ারেন্টাইনদের ভিডিও! নয়া ঘোষণা কর্ণাটক সরকারের"
evidence = "কর্ণাটক সরকারের নয়া সিদ্ধান্ত। কোয়ারেন্টাইনে থাকা ব্যক্তিদের প্রতি ঘণ্টায় সেলফি তুলে পাঠাতে হবে রাজ্য সরকারকে।"

inputs = tokenizer(
    evidence,
    text,
    return_tensors="pt",
    truncation=True,
    padding=True
)

with torch.no_grad():
    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)[0]
    prediction = torch.argmax(probs).item()

# Dynamically resolve label from model config
if hasattr(model, "config") and hasattr(model.config, "id2label") and model.config.id2label:
    id2lbl = model.config.id2label
    pred_label = id2lbl.get(prediction, id2lbl.get(str(prediction), "REFUTES" if prediction == 0 else "SUPPORTS"))
else:
    pred_label = "REFUTES" if prediction == 0 else "SUPPORTS"

print(f"Claim: {text}")
print(f"Evidence: {evidence}")
print(f"Predicted Veracity: {pred_label} (Confidence: {probs[prediction]*100:.2f}%)")