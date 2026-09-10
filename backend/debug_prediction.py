import json
from pathlib import Path
from app.services.claim_verifier import ClaimVerifier
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.pipeline import VerificationPipeline

verifier = ClaimVerifier()
verifier.load_model()
retriever = EvidenceRetriever()
retriever.build_index()
ranker = EvidenceRanker()
pipeline = VerificationPipeline(retriever=retriever, ranker=ranker, verifier=verifier)

with open('data/train_subtask1.json', encoding='utf-8') as f:
    data = json.load(f)

print('--- Testing latest 5 crawled items ---')
for item in data[-5:]:
    claim = item['Text']
    gold_label = item['Label']
    ev = item['Evidence']
    
    direct_pred = verifier.verify_pair(claim, ev)
    pipe_res = pipeline.run(claim)
    
    top_ev_text = pipe_res.evidence[0].text[:80] if pipe_res.evidence else "NONE"
    print(f"Claim: {claim[:80]}...")
    print(f"Gold Label: {gold_label}")
    print(f"Direct MuRIL (with exact evidence): {direct_pred}")
    print(f"Pipeline Verdict (with retrieval): {pipe_res.verdict} (conf: {pipe_res.confidence})")
    print(f"Top retrieved similarity: {pipe_res.evidence[0].retrieval_score if pipe_res.evidence else 0}")
    print(f"Top retrieved evidence: {top_ev_text}...")
    print("-----------------------------------------")
