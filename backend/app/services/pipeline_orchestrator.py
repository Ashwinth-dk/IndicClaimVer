"""
Pipeline Orchestrator — Multilingual end-to-end automation:
Crawl (EN/TA/HI/MR) → Extract → Validate → Accumulate → Train MuRIL → Evaluate (Per-Language) → Promote & Hot-Reload
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path

from app.services.scraper_service import ScraperService, CrawlRequest
from app.services.training_service import TrainingService
from app.storage.dataset_manager import DatasetManager
from app.storage.evidence_manager import EvidenceManager
from app.storage.source_manager import SourceManager
from app.storage.review_manager import ReviewManager


class PipelineStage:
    """Enum constants for pipeline stages."""
    QUEUED = "QUEUED"
    CRAWLING = "CRAWLING"
    PROCESSING = "PROCESSING"
    DATASET_BUILDING = "DATASET_BUILDING"
    DATA_QUALITY_VALIDATION = "DATA_QUALITY_VALIDATION"
    WAITING_FOR_TRAINING_THRESHOLD = "WAITING_FOR_TRAINING_THRESHOLD"
    TRAINING_QUEUED = "TRAINING_QUEUED"
    MU_RIL_TRAINING = "MU_RIL_TRAINING"
    MODEL_EVALUATION = "MODEL_EVALUATION"
    MODEL_ACTIVATION = "MODEL_ACTIVATION"
    TRAINING_SKIPPED = "TRAINING_SKIPPED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class PipelineOrchestrator:
    """
    Orchestrates the full multilingual crawl-to-train pipeline across English,
    Tamil, Hindi, and Marathi.
    """
    
    def __init__(
        self,
        dataset_manager: Optional[DatasetManager] = None,
        evidence_manager: Optional[EvidenceManager] = None,
        source_manager: Optional[SourceManager] = None,
        review_manager: Optional[ReviewManager] = None,
        rebuild_index_callback: Optional[Callable] = None,
        reload_model_callback: Optional[Callable] = None,
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        
        self.dataset_mgr = dataset_manager or DatasetManager()
        self.evidence_mgr = evidence_manager or EvidenceManager()
        self.source_mgr = source_manager or SourceManager()
        self.review_mgr = review_manager or ReviewManager()
        
        self.scraper = ScraperService(
            dataset_manager=self.dataset_mgr,
            evidence_manager=self.evidence_mgr,
            source_manager=self.source_mgr,
            review_manager=self.review_mgr
        )
        
        self.trainer = TrainingService(
            dataset_manager=self.dataset_mgr
        )
        
        self.rebuild_index_callback = rebuild_index_callback
        self.reload_model_callback = reload_model_callback
        
        # Pipeline state
        self.lock = threading.Lock()
        self.is_running = False
        self.current_job_id: Optional[str] = None
        self.current_stage: str = PipelineStage.QUEUED
        self.stage_details: str = ""
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.pipeline_thread: Optional[threading.Thread] = None
        
        # Results
        self.crawl_result: Dict[str, Any] = {}
        self.training_result: Dict[str, Any] = {}
        self.error_message: Optional[str] = None
        self.run_history: list = []
    
    def start_pipeline(
        self,
        topic: str,
        language: str = "all",
        target_count: int = 100,
        auto_train: bool = True,
        force_train: bool = False,
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
    ) -> Dict[str, Any]:
        with self.lock:
            if self.is_running:
                return {
                    "status": "error",
                    "message": "Pipeline is already running",
                    "job_id": self.current_job_id
                }
            
            self.is_running = True
            self.current_job_id = f"job_{str(uuid.uuid4())[:8]}"
            self.current_stage = PipelineStage.QUEUED
            self.stage_details = f"Initializing multilingual pipeline ({language})..."
            self.started_at = datetime.now().isoformat()
            self.completed_at = None
            self.crawl_result = {}
            self.training_result = {}
            self.error_message = None
        
        config = {
            "topic": topic,
            "language": language.lower().strip() if language else "all",
            "target_count": target_count,
            "auto_train": auto_train,
            "force_train": force_train,
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
        }
        
        self.pipeline_thread = threading.Thread(
            target=self._run_pipeline,
            args=(config,),
            daemon=True,
            name="PipelineOrchestrator"
        )
        self.pipeline_thread.start()
        
        return {
            "status": "success",
            "job_id": self.current_job_id,
            "message": f"Multilingual pipeline started for topic: '{topic}' ({config['language']})"
        }
    
    def trigger_training_only(
        self,
        epochs: int = 3,
        batch_size: int = 8,
        learning_rate: float = 2e-5,
    ) -> Dict[str, Any]:
        """Manual developer override to trigger training directly on accumulated data."""
        with self.lock:
            if self.is_running:
                return {
                    "status": "error",
                    "message": "A pipeline or training job is already running",
                    "job_id": self.current_job_id
                }
            
            self.is_running = True
            self.current_job_id = f"train_{str(uuid.uuid4())[:8]}"
            self.current_stage = PipelineStage.TRAINING_QUEUED
            self.stage_details = "Manual training override triggered by developer..."
            self.started_at = datetime.now().isoformat()
            self.completed_at = None
            self.crawl_result = {"collected": 0, "type": "manual_training_override"}
            self.training_result = {}
            self.error_message = None

        config = {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "force_train": True
        }

        self.pipeline_thread = threading.Thread(
            target=self._run_training_only,
            args=(config,),
            daemon=True,
            name="ManualTrainingJob"
        )
        self.pipeline_thread.start()

        return {
            "status": "success",
            "job_id": self.current_job_id,
            "message": "Multilingual training job initiated successfully"
        }

    def _run_training_only(self, config: Dict[str, Any]):
        try:
            self._update_stage(PipelineStage.DATA_QUALITY_VALIDATION, "Running Multilingual Quality Gate validation...")
            is_valid, reason, stats = self.trainer.validate_dataset()
            active_info = self.trainer.get_active_model_info()
            active_model_name = active_info.get("active_version", "baseline")

            if not is_valid:
                self._update_stage(PipelineStage.TRAINING_SKIPPED, f"Training skipped — {reason}")
                self.training_result = {
                    "training_status": "SKIPPED",
                    "status": "skipped",
                    "reason": reason,
                    "active_model": active_model_name,
                    "stats": stats
                }
                time.sleep(0.5)
                self._update_stage(
                    PipelineStage.COMPLETED,
                    f"Manual training skipped ({reason}). Active model '{active_model_name}' preserved."
                )
                self._finalize()
                return

            self._execute_training_flow(config, stats, active_model_name)
        except Exception as e:
            self._fail(str(e))

    def stop_pipeline(self) -> Dict[str, Any]:
        with self.lock:
            if not self.is_running:
                return {"status": "error", "message": "No pipeline is running"}
        
        self.scraper.stop_scraping()
        with self.lock:
            self.current_stage = PipelineStage.STOPPED
            self.stage_details = "Pipeline stopped by user"
        
        return {"status": "success", "message": "Stop signal sent to pipeline"}
    
    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            status = {
                "is_running": self.is_running,
                "job_id": self.current_job_id,
                "stage": self.current_stage,
                "stage_details": self.stage_details,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "error_message": self.error_message,
            }
        
        crawl_status = self.scraper.get_status()
        status["crawl_status"] = crawl_status
        status["language_statuses"] = crawl_status.get("language_statuses", {})
        
        if self.current_stage in [PipelineStage.MU_RIL_TRAINING, PipelineStage.MODEL_EVALUATION]:
            status["training_progress"] = self.trainer.get_training_progress()
        
        status["crawl_result"] = self.crawl_result
        status["training_result"] = self.training_result
        status["trigger_status"] = self.trainer.get_trigger_status()
        
        return status
    
    def get_history(self) -> list:
        return list(self.run_history)
    
    def _run_pipeline(self, config: Dict[str, Any]):
        try:
            # Stage 1: CRAWLING
            lang = config.get("language", "all")
            self._update_stage(PipelineStage.CRAWLING, f"Crawling multilingual sources for topic: '{config['topic']}' ({lang})")
            
            crawl_request = CrawlRequest(
                query=config["topic"],
                language=lang,
                label="balanced",
                target_count=config["target_count"],
                date_mode="both",
            )
            
            start_result = self.scraper.start_scraping(crawl_request)
            if start_result.get("status") == "error":
                self._fail(f"Crawl failed to start: {start_result.get('message')}")
                return
            
            while self.scraper.is_running:
                time.sleep(0.5)
                with self.lock:
                    if self.current_stage == PipelineStage.STOPPED:
                        return
            
            # Stage 2: PROCESSING
            self._update_stage(PipelineStage.PROCESSING, "Processing and validating extracted multilingual records...")
            time.sleep(0.2)
            
            crawl_status = self.scraper.get_status()
            collected_count = crawl_status.get("collected_count", 0)
            self.crawl_result = {
                "collected": collected_count,
                "supports": crawl_status.get("supports_count", 0),
                "refutes": crawl_status.get("refutes_count", 0),
                "rejected": crawl_status.get("rejected_count", 0),
                "language_counts": crawl_status.get("language_counts", {}),
                "language_statuses": crawl_status.get("language_statuses", {}),
                "urls_crawled": crawl_status.get("urls_crawled", 0),
            }
            
            # Stage 3: DATASET_BUILDING
            self._update_stage(PipelineStage.DATASET_BUILDING, "Consolidating and deduplicating multilingual dataset...")
            dataset_stats = self.dataset_mgr.get_stats()
            self.crawl_result["total_dataset_size"] = dataset_stats["total_count"]
            self.crawl_result["dataset_languages"] = dataset_stats.get("languages", {})
            time.sleep(0.2)

            if self.rebuild_index_callback and collected_count > 0:
                try:
                    self.rebuild_index_callback()
                except Exception as e:
                    print(f"[PipelineOrchestrator] Evidence index rebuild notice: {e}")

            # Accumulate new examples counter
            self.trainer.increment_new_examples(collected_count)
            trigger_status = self.trainer.get_trigger_status()
            new_accumulated = trigger_status["new_examples_since_last_training"]
            threshold = trigger_status["threshold"]
            auto_train_enabled = trigger_status["auto_train_enabled"] and config.get("auto_train", True)
            force_train = config.get("force_train", False)
            active_info = self.trainer.get_active_model_info()
            active_model_name = active_info.get("active_version", "baseline")

            if not force_train and (not auto_train_enabled or new_accumulated < threshold):
                self._update_stage(
                    PipelineStage.WAITING_FOR_TRAINING_THRESHOLD,
                    f"Multilingual dataset updated (+{collected_count} items). Total new data: {new_accumulated}/{threshold}. Training threshold not reached."
                )
                self.training_result = {
                    "training_status": "WAITING_FOR_TRAINING_THRESHOLD",
                    "status": "waiting_for_threshold",
                    "new_examples": new_accumulated,
                    "threshold": threshold,
                    "remaining_needed": max(0, threshold - new_accumulated),
                    "active_model": active_model_name
                }
                time.sleep(0.5)
                self._update_stage(
                    PipelineStage.COMPLETED,
                    f"Pipeline complete: +{collected_count} records accumulated (Total: {dataset_stats['total_count']}). Waiting for {max(0, threshold - new_accumulated)} more valid examples for auto-retraining."
                )
                self._finalize()
                return

            # Stage 4: DATA_QUALITY_VALIDATION
            self._update_stage(PipelineStage.DATA_QUALITY_VALIDATION, "Threshold reached. Running Multilingual Quality Gate...")
            is_valid, reason, stats = self.trainer.validate_dataset()
            
            if not is_valid:
                self._update_stage(PipelineStage.TRAINING_SKIPPED, f"Training skipped — {reason}")
                self.training_result = {
                    "training_status": "SKIPPED",
                    "status": "skipped",
                    "reason": reason,
                    "active_model": active_model_name,
                    "stats": stats
                }
                time.sleep(0.5)
                self._update_stage(
                    PipelineStage.COMPLETED,
                    f"Pipeline complete: Crawl data collected. Training skipped ({reason}). Active model '{active_model_name}' preserved."
                )
                self._finalize()
                return
            
            # Execute Training Flow
            self._execute_training_flow(config, stats, active_model_name)
            
        except Exception as e:
            self._fail(str(e))

    def _execute_training_flow(self, config: Dict[str, Any], stats: Dict[str, Any], active_model_name: str):
        try:
            self._update_stage(PipelineStage.TRAINING_QUEUED, "Queuing MuRIL automated fine-tuning job...")
            time.sleep(0.3)
            self._update_stage(PipelineStage.MU_RIL_TRAINING, f"Fine-tuning MuRIL model ({stats['total']} valid multilingual examples)...")
            
            def training_progress_cb(stage, progress, detail):
                if stage == "evaluating":
                    self._update_stage(PipelineStage.MODEL_EVALUATION, f"Evaluating multilingual model checkpoint ({detail})...")
                else:
                    self._update_stage(PipelineStage.MU_RIL_TRAINING, detail)
            
            training_result = self.trainer.train(
                epochs=config.get("epochs", 3),
                batch_size=config.get("batch_size", 8),
                learning_rate=config.get("learning_rate", 2e-5),
                progress_callback=training_progress_cb
            )
            
            if training_result.get("status") == "activated":
                self._update_stage(PipelineStage.MODEL_ACTIVATION, f"Activating new model version '{training_result.get('version')}'...")
                
                if self.reload_model_callback:
                    try:
                        self.reload_model_callback(training_result.get("model_path"))
                    except Exception as e:
                        print(f"[PipelineOrchestrator] Model hot-reload notice: {e}")
                
                self.training_result = {
                    "training_status": "ACTIVATED",
                    "status": "activated",
                    "version": training_result.get("version"),
                    "active_model": training_result.get("version"),
                    "metrics": training_result.get("metrics", {}),
                    "model_path": training_result.get("model_path"),
                    "stats": stats
                }
                self._update_stage(
                    PipelineStage.COMPLETED,
                    f"Pipeline completed successfully. Model {training_result.get('version')} evaluated and activated (Acc={training_result.get('metrics', {}).get('test_accuracy', 'N/A')}, F1={training_result.get('metrics', {}).get('macro_f1', 'N/A')})."
                )
            elif training_result.get("status") == "skipped":
                self._update_stage(PipelineStage.TRAINING_SKIPPED, f"Training skipped: {training_result.get('message')}")
                self.training_result = {
                    "training_status": "SKIPPED",
                    "status": "skipped",
                    "reason": training_result.get("message"),
                    "active_model": active_model_name,
                    "stats": stats
                }
                time.sleep(0.5)
                self._update_stage(PipelineStage.COMPLETED, f"Pipeline complete. Training skipped: {training_result.get('message')}")
            else:
                self.training_result = {
                    "training_status": "NOT_ACTIVATED",
                    "status": "not_activated",
                    "reason": training_result.get("message", "Model did not meet activation criteria"),
                    "active_model": active_model_name,
                    "metrics": training_result.get("metrics", {}),
                    "stats": stats
                }
                self._update_stage(
                    PipelineStage.COMPLETED,
                    f"Pipeline complete. Training finished but model not activated (active: {active_model_name}): {training_result.get('message')}"
                )
            
            self._finalize()
                
        except Exception as e:
            self._fail(str(e))
    
    def _update_stage(self, stage: str, details: str):
        with self.lock:
            self.current_stage = stage
            self.stage_details = details
    
    def _fail(self, message: str):
        with self.lock:
            self.current_stage = PipelineStage.FAILED
            self.stage_details = message
            self.error_message = message
            self.is_running = False
            self.completed_at = datetime.now().isoformat()
        self._save_history()
    
    def _finalize(self):
        with self.lock:
            self.is_running = False
            self.completed_at = datetime.now().isoformat()
        self._save_history()
    
    def _save_history(self):
        record = {
            "job_id": self.current_job_id,
            "stage": self.current_stage,
            "stage_details": self.stage_details,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "crawl_result": dict(self.crawl_result),
            "training_result": dict(self.training_result),
            "error_message": self.error_message
        }
        self.run_history.append(record)
        if len(self.run_history) > 20:
            self.run_history = self.run_history[-20:]
