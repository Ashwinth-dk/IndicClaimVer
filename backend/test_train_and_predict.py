import os
import json
import torch
from pathlib import Path
from app.services.training_service import TrainingService
from app.services.claim_verifier import ClaimVerifier

print("=" * 60)
print("TESTING TRAINING AND PREDICTION ON CRAWLED DATA")
print("=" * 60)

trainer = TrainingService()
print("Validating dataset...")
is_valid, reason, stats = trainer.validate_dataset()
print(f"Validation: {is_valid} ({reason})")
print(f"Stats: {stats}")

# Train for 2 epochs on the accumulated dataset
print("\nStarting MuRIL fine-tuning (2 epochs)...")
result = trainer.train(epochs=2, batch_size=16, learning_rate=3e-5)
print(f"Training Result: {result.get('status')} - {result.get('message')}")
print(f"Metrics: {result.get('metrics')}")

if result.get("status") == "activated":
    print("\nModel activated! Testing newly trained model on crawled samples...")
    verifier = ClaimVerifier()
    verifier.load_model()
    
    with open("data/train_subtask1.json", encoding="utf-8") as f:
        data = json.load(f)
    
    correct = 0
    total = 10
    samples = data[-10:]
    
    for item in samples:
        claim = item.get("Text", "")
        ev = item.get("Evidence", "")
        gold = item.get("Label", "")
        
        if not claim or not ev:
            continue
            
        pred = verifier.verify_pair(claim, ev)
        is_match = (pred["prediction"] == gold)
        if is_match:
            correct += 1
            
        print(f"\n[ID: {item.get('ID')}] Gold: {gold} | Pred: {pred['prediction']} (conf: {pred['confidence']}) -> {'MATCH' if is_match else 'MISMATCH'}")
        print(f"  Claim:    {claim[:70].encode('ascii', 'ignore').decode()}...")
        print(f"  Evidence: {ev[:70].encode('ascii', 'ignore').decode()}...")
        
    print(f"\nAccuracy on recent crawled samples: {correct}/{len(samples)} ({correct/len(samples)*100:.1f}%)")
