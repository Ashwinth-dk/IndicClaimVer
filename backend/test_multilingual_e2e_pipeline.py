"""
End-to-End Multilingual Pipeline Test for IndicClaim.
Executes and validates the full multilingual pipeline:
COLLECT -> VALIDATE -> STORE -> LEARN -> EVALUATE -> PROMOTE -> SERVE
across English (en), Tamil (ta), Hindi (hi), and Marathi (mr).
"""

import sys
import os
import json
import time
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.utils.language_detector import LanguageDetector
from app.storage.dataset_manager import DatasetManager
from app.storage.evidence_manager import EvidenceManager
from app.storage.source_manager import SourceManager
from app.storage.review_manager import ReviewManager
from app.services.training_service import TrainingService
from app.services.claim_verifier import ClaimVerifier
from app.services.evidence_retriever import EvidenceRetriever
from app.services.evidence_ranker import EvidenceRanker
from app.services.pipeline import VerificationPipeline
from app.config import (
    MODEL_PATH,
    LABEL_MAPPING_PATH,
    EVIDENCE_POOL_PATH,
    EMBEDDINGS_CACHE_PATH,
    EMBEDDING_MODEL_NAME,
    DEVICE,
    TOP_K
)

def run_multilingual_e2e_test():
    print("=" * 70)
    print("INDICCLAIM: END-TO-END MULTILINGUAL PIPELINE VERIFICATION")
    print("Languages: English (en), Tamil (ta), Hindi (hi), Marathi (mr)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # STEP 1: VERIFY MULTILINGUAL DATASET & QUALITY GATE
    # -------------------------------------------------------------------------
    print("\n[STEP 1] Validating Multilingual Dataset Distribution...")
    dm = DatasetManager()
    stats = dm.get_stats()
    print(f"  Total items:    {stats['total_count']}")
    print(f"  SUPPORTS:       {stats['supports_count']}")
    print(f"  REFUTES:        {stats['refutes_count']}")
    print(f"  Balance ratio:  {stats['balance_ratio']}")
    print(f"  Languages:      {stats.get('languages', {})}")

    ts = TrainingService()
    is_valid, qg_reason, qg_stats = ts.validate_dataset()
    print(f"  Quality Gate:   {'PASSED' if is_valid else 'FAILED'} -> {qg_reason}")
    assert is_valid, f"Quality Gate failed: {qg_reason}"

    # -------------------------------------------------------------------------
    # STEP 2: AUTOMATIC RETRAINING TRIGGER TEST
    # -------------------------------------------------------------------------
    print("\n[STEP 2] Verifying Automated Training Trigger & Lock Mechanisms...")
    trigger_status = ts.get_trigger_status()
    print(f"  Active Version:    {trigger_status['active_version']}")
    print(f"  New data count:    {trigger_status['new_examples_since_last_training']}")
    print(f"  Retrain threshold: {trigger_status['threshold']}")
    print(f"  Auto-train state:  {trigger_status['auto_train_enabled']}")

    # Temporarily set threshold to test trigger
    ts.set_retrain_threshold(10)
    ts.increment_new_examples(15)
    trig_after = ts.get_trigger_status()
    print(f"  Threshold reached: {trig_after['is_threshold_reached']} (New: {trig_after['new_examples_since_last_training']} >= {trig_after['threshold']})")
    assert trig_after['is_threshold_reached'], "Automatic retrain threshold trigger failed!"

    # -------------------------------------------------------------------------
    # STEP 3: TRAIN MURIL MULTILINGUAL MODEL
    # -------------------------------------------------------------------------
    print("\n[STEP 3] Fine-Tuning MuRIL on Multilingual Dataset (Stratified across EN, TA, HI, MR)...")
    start_train_time = time.time()
    
    def progress_callback(stage, progress, detail):
        print(f"    [{stage.upper()}] ({progress}%): {detail}")

    train_result = ts.train(
        epochs=3,
        batch_size=8,
        learning_rate=3e-5,
        progress_callback=progress_callback
    )
    
    train_duration = time.time() - start_train_time
    print(f"\n  Training Result: {train_result.get('status')} in {train_duration:.1f}s")
    print(f"  Message:         {train_result.get('message')}")
    print(f"  New Version:     {train_result.get('version', 'N/A')}")
    
    assert train_result.get("status") == "activated", f"Training/Activation failed: {train_result}"

    # -------------------------------------------------------------------------
    # STEP 4: MULTILINGUAL MODEL EVALUATION & PER-LANGUAGE METRICS
    # -------------------------------------------------------------------------
    print("\n[STEP 4] Multilingual Model Evaluation & Regression Analysis...")
    metrics = train_result.get("metrics", {})
    overall = metrics.get("overall", {})
    per_lang = metrics.get("per_language", {})

    print("\n  OVERALL TEST PERFORMANCE:")
    print(f"    Overall Accuracy:   {metrics.get('test_accuracy', 0.0):.4f}")
    print(f"    Overall Macro F1:   {metrics.get('macro_f1', 0.0):.4f}")
    print(f"    SUPPORTS F1:        {overall.get('supports_f1', 0.0):.4f} (Precision: {overall.get('supports_precision', 0.0):.4f}, Recall: {overall.get('supports_recall', 0.0):.4f})")
    print(f"    REFUTES F1:         {overall.get('refutes_f1', 0.0):.4f} (Precision: {overall.get('refutes_precision', 0.0):.4f}, Recall: {overall.get('refutes_recall', 0.0):.4f})")

    print("\n  PER-LANGUAGE PERFORMANCE:")
    for lang_code in ["en", "ta", "hi", "mr"]:
        l_info = per_lang.get(lang_code, {})
        lang_name = LanguageDetector.SUPPORTED_LANGUAGES.get(lang_code, lang_code.upper())
        print(f"    {lang_name:<10} ({lang_code}): Accuracy={l_info.get('accuracy', 0.0):.4f}, Macro F1={l_info.get('macro_f1', 0.0):.4f}, Samples={l_info.get('count', 0)}")

    # -------------------------------------------------------------------------
    # STEP 5: VERIFY MODEL METADATA & IMMUTABLE VERSIONING
    # -------------------------------------------------------------------------
    print("\n[STEP 5] Verifying Model Versioning & Metadata Persistence...")
    active_info = ts.get_active_model_info()
    new_active_version = active_info.get("active_version")
    print(f"  Active Version in metadata: {new_active_version}")
    print(f"  Model Path in metadata:     {active_info.get('model_path')}")
    print(f"  Version History Length:     {len(active_info.get('history', []))}")
    assert new_active_version == train_result.get("version"), "Active model version was not updated in model_metadata.json!"

    # -------------------------------------------------------------------------
    # STEP 6: HOT-RELOAD INFERENCE TEST IN ALL 4 LANGUAGES
    # -------------------------------------------------------------------------
    print("\n[STEP 6] Hot-Reloading Active Model and Testing Multilingual Live Inference...")
    verifier = ClaimVerifier()
    verifier.reload_active_model()
    print(f"  Hot-reloaded model from: {verifier.model_path.name}")

    # Build or load retriever
    retriever = EvidenceRetriever(
        pool_path=EVIDENCE_POOL_PATH,
        cache_path=EMBEDDINGS_CACHE_PATH,
        model_name=EMBEDDING_MODEL_NAME,
        device=DEVICE
    )
    retriever.build_index()
    ranker = EvidenceRanker(top_k=TOP_K)
    pipeline = VerificationPipeline(retriever=retriever, ranker=ranker, verifier=verifier)

    test_multilingual_claims = [
        # English
        {
            "lang": "en",
            "claim": "Election Commission of India introduced voter verifiable paper audit trail (VVPAT) for all electronic voting machines.",
            "expected_verdict": "SUPPORTS"
        },
        {
            "lang": "en",
            "claim": "Government of India announced the complete privatization of all nationalized public sector banks.",
            "expected_verdict": "REFUTES"
        },
        # Tamil
        {
            "lang": "ta",
            "claim": "இந்திய விண்வெளி ஆராய்ச்சி நிறுவனம் (இஸ்ரோ) சந்திரயான்-3 விண்கலத்தை நிலவின் தென் துருவத்தில் வெற்றிகரமாக தரையிறக்கியது.",
            "expected_verdict": "SUPPORTS"
        },
        {
            "lang": "ta",
            "claim": "இந்தியாவில் 500 ரூபாய் நோட்டுகள் அனைத்தும் செல்லாது என மத்திய அரசு அறிவித்துள்ளது.",
            "expected_verdict": "REFUTES"
        },
        # Hindi
        {
            "lang": "hi",
            "claim": "सुप्रीम कोर्ट ने चुनावी बॉन्ड योजना को असंवैधानिक घोषित करते हुए पूरी तरह से रद्द कर दिया।",
            "expected_verdict": "SUPPORTS"
        },
        {
            "lang": "hi",
            "claim": "केंद्र सरकार ने सभी केंद्रीय कर्मचारियों के लिए 8वें वेतन आयोग का गठन कर दिया है।",
            "expected_verdict": "REFUTES"
        },
        # Marathi
        {
            "lang": "mr",
            "claim": "महाराष्ट्र शासनाने महिलांसाठी 'मुख्यमंत्री माझी लाडकी बहीण योजना' सुरू केली आहे.",
            "expected_verdict": "SUPPORTS"
        },
        {
            "lang": "mr",
            "claim": "महाराष्ट्र राज्य मार्ग परिवहन महामंडळाने सर्व ज्येष्ठ नागरिकांसाठी मोफत प्रवास योजना बंद केली आहे.",
            "expected_verdict": "REFUTES"
        }
    ]

    print("\n  RUNNING LIVE MULTILINGUAL INFERENCE TEST SUITE:")
    passed_inferences = 0

    for idx, tc in enumerate(test_multilingual_claims, start=1):
        claim_text = tc["claim"]
        exp_verdict = tc["expected_verdict"]
        lang = tc["lang"]

        response = pipeline.run(claim_text)
        pred_verdict = response.verdict
        confidence = response.confidence
        det_lang = response.language
        model_v = response.model_version

        is_match = (pred_verdict == exp_verdict)
        if is_match:
            passed_inferences += 1

        print(f"\n  [{idx}] [{lang.upper()}] Expected: {exp_verdict} | Model Prediction: {pred_verdict} ({confidence*100:.1f}% conf)")
        print(f"      Claim:    {claim_text[:80]}...")
        print(f"      Language: {det_lang} (Detected) | Model: {model_v}")
        print(f"      Summary:  {response.summary[:100]}...")
        print(f"      Status:   {'PASSED' if is_match else 'MISMATCH'}")

    print("\n" + "=" * 70)
    print(f"MULTILINGUAL PIPELINE VERIFICATION COMPLETE: {passed_inferences}/{len(test_multilingual_claims)} Inferences Validated")
    print("=" * 70)

    assert passed_inferences == len(test_multilingual_claims), f"Some multilingual inferences failed ({passed_inferences}/{len(test_multilingual_claims)})"
    print("\nALL MULTILINGUAL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_multilingual_e2e_test()
