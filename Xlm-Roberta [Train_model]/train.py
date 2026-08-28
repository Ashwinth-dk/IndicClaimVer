import os
import sys
import io
import json
import pandas as pd
import numpy as np
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer
)
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_NAME = "xlm-roberta-base"
TRAIN_FILE = BASE_DIR / "dataset" / "train_subtask1.json"
DEV_FILE = BASE_DIR / "dataset" / "dev_subtask1.json"
SAVE_MODEL_PATH = BASE_DIR / "saved_model"

MAX_LENGTH = 128
BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5

label2id = {
    "SUPPORTS": 0,
    "REFUTES": 1,
    "NOT ENOUGH INFO": 2
}

id2label = {
    0: "SUPPORTS",
    1: "REFUTES",
    2: "NOT ENOUGH INFO"
}

def load_json(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for item in data:
        rows.append({
            "text": item["Text"],
            "evidence": item["Evidence"],
            "label": label2id[item["Label"]]
        })
    return pd.DataFrame(rows)

print(f"Loading data from {TRAIN_FILE} and {DEV_FILE}...")
train_df = load_json(TRAIN_FILE)
dev_df = load_json(DEV_FILE)

print(f"Train samples: {len(train_df)} | Dev samples: {len(dev_df)}")

train_dataset = Dataset.from_pandas(train_df)
dev_dataset = Dataset.from_pandas(dev_df)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

def tokenize(batch):
    return tokenizer(
        batch["evidence"],
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=MAX_LENGTH
    )

train_dataset = train_dataset.map(tokenize, batched=True)
dev_dataset = dev_dataset.map(tokenize, batched=True)

columns = ["input_ids", "attention_mask", "label"]
train_dataset.set_format(type="torch", columns=columns)
dev_dataset.set_format(type="torch", columns=columns)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME,
    num_labels=3,
    id2label=id2label,
    label2id=label2id
)

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        average="weighted",
        zero_division=0
    )
    acc = accuracy_score(labels, predictions)
    return {
        "accuracy": acc,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

# Compatibility for eval_strategy
strategy_kwargs = {}
try:
    TrainingArguments(output_dir="./results", eval_strategy="epoch")
    strategy_kwargs["eval_strategy"] = "epoch"
except TypeError:
    strategy_kwargs["evaluation_strategy"] = "epoch"

training_args = TrainingArguments(
    output_dir="./results",
    save_strategy="epoch",
    learning_rate=LEARNING_RATE,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    greater_is_better=True,
    fp16=False,
    **strategy_kwargs
)

trainer_kwargs = {
    "model": model,
    "args": training_args,
    "train_dataset": train_dataset,
    "eval_dataset": dev_dataset,
    "compute_metrics": compute_metrics
}
try:
    trainer = Trainer(processing_class=tokenizer, **trainer_kwargs)
except TypeError:
    trainer = Trainer(tokenizer=tokenizer, **trainer_kwargs)

print("Starting training loop...")
trainer.train()

SAVE_MODEL_PATH.mkdir(parents=True, exist_ok=True)
trainer.save_model(str(SAVE_MODEL_PATH))
tokenizer.save_pretrained(str(SAVE_MODEL_PATH))

print(f"Training completed! Model weights saved to {SAVE_MODEL_PATH}")