import sys
import torch
import torch.nn.functional as F
from transformers import BertTokenizerFast, BertForSequenceClassification
from pathlib import Path

model_path = Path("models/muril_claim_verification_model")
tokenizer = BertTokenizerFast.from_pretrained(str(model_path))
model = BertForSequenceClassification.from_pretrained(str(model_path))
model.eval()

test_cases = [
    {
        "type": "OBVIOUS_SUPPORT",
        "claim": "The college is affiliated with Anna University.",
        "evidence": "Kongu Engineering College is affiliated with Anna University and approved by AICTE."
    },
    {
        "type": "IDENTICAL_TEXT_SUPPORT",
        "claim": "India won the cricket world cup in 2011.",
        "evidence": "India won the cricket world cup in 2011 after defeating Sri Lanka in the finals."
    },
    {
        "type": "OBVIOUS_REFUTE",
        "claim": "The college is located in Mumbai.",
        "evidence": "The college is located in Perundurai, Erode, Tamil Nadu, and has no campus in Mumbai."
    },
    {
        "type": "OBVIOUS_REFUTE_2",
        "claim": "The earth is flat.",
        "evidence": "Scientific consensus and satellite imagery prove that the Earth is an oblate spheroid, debunking flat earth claims."
    }
]

print("=" * 60)
print("TESTING RAW LOGITS AND ORDERINGS")
print("=" * 60)

for tc in test_cases:
    claim = tc["claim"]
    ev = tc["evidence"]
    
    # 1. Order (claim, evidence)
    inp1 = tokenizer(claim, ev, return_tensors="pt", max_length=256, truncation=True, padding=True)
    with torch.no_grad():
        out1 = model(**inp1)
        logits1 = out1.logits[0].tolist()
        probs1 = F.softmax(out1.logits[0], dim=-1).tolist()
    
    # 2. Order (evidence, claim)
    inp2 = tokenizer(ev, claim, return_tensors="pt", max_length=256, truncation=True, padding=True)
    with torch.no_grad():
        out2 = model(**inp2)
        logits2 = out2.logits[0].tolist()
        probs2 = F.softmax(out2.logits[0], dim=-1).tolist()
        
    print(f"\nTest Type: {tc['type']}")
    print(f"Claim:    {claim}")
    print(f"Evidence: {ev}")
    print(f"  [claim, evidence] -> Logits: [0]={logits1[0]:.4f}, [1]={logits1[1]:.4f} | Probs: [0]={probs1[0]:.4f}, [1]={probs1[1]:.4f}")
    print(f"  [evidence, claim] -> Logits: [0]={logits2[0]:.4f}, [1]={logits2[1]:.4f} | Probs: [0]={probs2[0]:.4f}, [1]={probs2[1]:.4f}")
