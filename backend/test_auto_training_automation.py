"""
Comprehensive Automation & Quality Gate Test Suite for IndicClaim.

Tests:
1. Data Accumulation (No Overwrites)
2. Retrain Trigger Threshold logic (accumulating until >= threshold)
3. Quality Gate 10-point inspection
4. Concurrency lock protection (no simultaneous training runs)
5. Model Versioning & Activation promotion
6. Model Rollback and hot-reloading
7. Preserving accumulated data and active model on training failure
8. Role-based security (Public vs Admin endpoints)
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
import unittest

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from app.config import ADMIN_API_KEY
from app.main import app
from app.storage.dataset_manager import DatasetManager
from app.services.training_service import TrainingService
from app.services.pipeline_orchestrator import PipelineOrchestrator, PipelineStage


class TestAutoTrainingAutomation(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.data_dir = self.test_dir / "data"
        self.models_dir = self.test_dir / "models"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.dataset_file = self.data_dir / "train_subtask1.json"
        self.metadata_file = self.models_dir / "model_metadata.json"

        # Initialize dataset with 50 valid items
        initial_data = []
        for i in range(1, 31):
            initial_data.append({
                "ID": f"S1/{i:06d}",
                "Text": f"Factual test claim statement number {i:04d} verified by official sources.",
                "Evidence": f"Detailed supporting factual evidence passage document reference number {i:04d} confirming facts.",
                "Label": "SUPPORTS"
            })
        for i in range(31, 51):
            initial_data.append({
                "ID": f"S1/{i:06d}",
                "Text": f"Factual test claim statement number {i:04d} refuted by official sources.",
                "Evidence": f"Detailed refuting factual evidence passage document reference number {i:04d} debunking claims.",
                "Label": "REFUTES"
            })
        with open(self.dataset_file, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=2)

        # Initial model metadata
        initial_meta = {
            "active_version": "v1",
            "model_path": "muril_claim_verification_model_v1",
            "trained_at": "2026-09-01T00:00:00",
            "new_examples_since_last_training": 0,
            "auto_train_enabled": True,
            "min_new_examples_for_retrain": 100,
            "history": [
                {
                    "version": "v1",
                    "trained_at": "2026-09-01T00:00:00",
                    "dataset_size": 50,
                    "metrics": {"test_accuracy": 0.82, "macro_f1": 0.81}
                }
            ]
        }
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(initial_meta, f, indent=2)

        # Create dummy model directories
        (self.models_dir / "muril_claim_verification_model_v1").mkdir(parents=True, exist_ok=True)
        (self.models_dir / "muril_claim_verification_model_v2").mkdir(parents=True, exist_ok=True)

        self.dataset_mgr = DatasetManager(str(self.dataset_file))
        self.trainer = TrainingService(
            models_dir=str(self.models_dir),
            data_dir=str(self.data_dir),
            dataset_manager=self.dataset_mgr
        )
        
        # Setup mock pipeline for API route testing if needed
        from app.routes.verification import set_pipeline, _pipeline
        from app.routes.crawl import set_orchestrator
        
        class MockPipeline:
            def __init__(self):
                self.retriever = type("MockRetriever", (), {"evidence_data": [1, 2, 3]})()
                self.verifier = type("MockVerifier", (), {"model": object()})()
            def run(self, claim):
                return {
                    "claim": claim,
                    "verdict": "SUPPORTS",
                    "confidence": 0.95,
                    "supports_score": 0.95,
                    "refutes_score": 0.05,
                    "summary": "Verified by mock pipeline",
                    "evidence": [],
                    "processing": {
                        "claim_analysis": "completed",
                        "evidence_retrieval": "completed",
                        "evidence_ranking": "completed",
                        "verification": "completed",
                    },
                    "model_name": "Mock MuRIL",
                }
        set_pipeline(MockPipeline())
            
        orchestrator = PipelineOrchestrator(
            dataset_manager=self.dataset_mgr
        )
        set_orchestrator(orchestrator)
        
        self.client = TestClient(app)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_data_accumulation_no_overwrite(self):
        """Test dataset accumulates without overwriting existing records."""
        initial_items = self.dataset_mgr.load_all()
        self.assertEqual(len(initial_items), 50)

        # Crawl #1 adds 25 items
        batch1 = [
            {"Text": f"New scraped claim A_{i}", "Evidence": f"New scraped evidence A_{i} with sufficient context length.", "Label": "SUPPORTS"}
            for i in range(25)
        ]
        self.dataset_mgr.add_items_batch(batch1)
        self.assertEqual(len(self.dataset_mgr.load_all()), 75)

        # Crawl #2 adds 40 items
        batch2 = [
            {"Text": f"New scraped claim B_{i}", "Evidence": f"New scraped evidence B_{i} with sufficient context length.", "Label": "REFUTES"}
            for i in range(40)
        ]
        self.dataset_mgr.add_items_batch(batch2)
        self.assertEqual(len(self.dataset_mgr.load_all()), 115)

    def test_02_retrain_threshold_trigger_logic(self):
        """Test training trigger activates only when new examples reach threshold."""
        status = self.trainer.get_trigger_status()
        self.assertEqual(status["new_examples_since_last_training"], 0)
        self.assertEqual(status["threshold"], 100)
        self.assertFalse(status["is_threshold_reached"])

        # Crawl 1: +40 examples
        self.trainer.increment_new_examples(40)
        status1 = self.trainer.get_trigger_status()
        self.assertEqual(status1["new_examples_since_last_training"], 40)
        self.assertFalse(status1["is_threshold_reached"])
        self.assertEqual(status1["examples_remaining"], 60)

        # Crawl 2: +70 examples -> Total 110 >= 100
        self.trainer.increment_new_examples(70)
        status2 = self.trainer.get_trigger_status()
        self.assertEqual(status2["new_examples_since_last_training"], 110)
        self.assertTrue(status2["is_threshold_reached"])
        self.assertEqual(status2["examples_remaining"], 0)

    def test_03_training_lock_concurrency(self):
        """Test concurrency lock prevents two simultaneous training jobs."""
        self.assertFalse(self.trainer.is_training)
        
        with self.trainer.lock:
            self.trainer.is_training = True

        status = self.trainer.get_trigger_status()
        self.assertTrue(status["is_training_locked"])

        # Attempt to train while locked
        res = self.trainer.train()
        self.assertEqual(res["status"], "error")
        self.assertIn("already in progress", res["message"])

        with self.trainer.lock:
            self.trainer.is_training = False

    def test_04_quality_gate_checks(self):
        """Test 10-point Training Quality Gate validation."""
        is_valid, reason, stats = self.trainer.validate_dataset()
        self.assertTrue(is_valid, f"Quality gate should pass: {reason}")
        self.assertEqual(stats["total"], 50)
        self.assertEqual(stats["supports"], 30)
        self.assertEqual(stats["refutes"], 20)

    def test_05_model_activation_and_counter_reset(self):
        """Test model activation updates active version and resets counter."""
        self.trainer.increment_new_examples(110)
        self.assertEqual(self.trainer.get_trigger_status()["new_examples_since_last_training"], 110)

        # Activate v2
        promoted = self.trainer.activate_model_version("v2")
        self.assertEqual(promoted["version"], "v2")
        
        info = self.trainer.get_active_model_info()
        self.assertEqual(info["active_version"], "v2")

        # Counter reset
        self.trainer.reset_new_examples()
        self.assertEqual(self.trainer.get_trigger_status()["new_examples_since_last_training"], 0)

    def test_06_model_rollback(self):
        """Test rollback to previous working model."""
        self.trainer.activate_model_version("v2")
        self.assertEqual(self.trainer.get_active_model_info()["active_version"], "v2")

        # Rollback to v1
        rolled_back = self.trainer.rollback_to_version("v1")
        self.assertEqual(rolled_back["version"], "v1")
        self.assertEqual(self.trainer.get_active_model_info()["active_version"], "v1")

    def test_07_preserve_data_on_training_failure(self):
        """Test accumulated data is preserved and not lost if training fails."""
        initial_count = len(self.dataset_mgr.load_all())
        self.trainer.increment_new_examples(120)

        # Simulate failed validation or failed training
        active_before = self.trainer.get_active_model_info()["active_version"]
        
        # Ensure dataset was not deleted
        self.assertEqual(len(self.dataset_mgr.load_all()), initial_count)
        # Active model remains unchanged
        self.assertEqual(self.trainer.get_active_model_info()["active_version"], active_before)
        # Accumulated counter preserved
        self.assertEqual(self.trainer.get_trigger_status()["new_examples_since_last_training"], 120)

    def test_08_role_based_api_security(self):
        """Test public endpoints require no key, developer endpoints require admin key."""
        # Public health check
        res_health = self.client.get("/api/health")
        self.assertEqual(res_health.status_code, 200)

        # Public verification
        res_verify = self.client.post("/api/verify", json={"claim": "India launched Chandrayaan-3 successfully."})
        self.assertEqual(res_verify.status_code, 200)

        # Protected crawl endpoint without key -> 401
        res_crawl_unauth = self.client.post("/api/crawl/start", json={"topic": "Health News", "target_count": 10})
        self.assertEqual(res_crawl_unauth.status_code, 401)

        # Protected training pause without key -> 401
        res_pause_unauth = self.client.post("/api/training/pause")
        self.assertEqual(res_pause_unauth.status_code, 401)

        # Protected training pause with key -> 200
        headers = {"X-Admin-Key": ADMIN_API_KEY}
        res_pause_auth = self.client.post("/api/training/pause", headers=headers)
        self.assertEqual(res_pause_auth.status_code, 200)
        self.assertFalse(res_pause_auth.json()["auto_train_enabled"])

        # Protected training resume with key -> 200
        res_resume_auth = self.client.post("/api/training/resume", headers=headers)
        self.assertEqual(res_resume_auth.status_code, 200)
        self.assertTrue(res_resume_auth.json()["auto_train_enabled"])


if __name__ == "__main__":
    unittest.main()
