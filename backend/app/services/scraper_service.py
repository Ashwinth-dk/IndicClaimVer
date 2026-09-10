import asyncio
import threading
import time
import uuid
import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Tuple

from app.storage.dataset_manager import DatasetManager
from app.storage.evidence_manager import EvidenceManager
from app.storage.source_manager import SourceManager
from app.storage.review_manager import ReviewManager

from app.crawlers.async_crawler import AsyncCrawler
from app.crawlers.async_search_engine import AsyncSearchEngine
from app.extractors.claim_extractor import ClaimExtractor
from app.extractors.evidence_extractor import EvidenceExtractor
from app.verification.candidate_matcher import CandidateMatcher
from app.verification.label_generator import LabelGenerator
from app.verification.duplicate_detector import DuplicateDetector
from app.verification.quality_checker import QualityChecker
from app.crawlers.query_intent import QueryIntent, QueryIntentAnalyzer
from app.crawlers.topic_filter import TopicRelevanceFilter, QueryRelevanceDiagnostics
from app.utils.language_detector import LanguageDetector


class CrawlRequest:
    """Multilingual crawl request supporting English, Tamil, Hindi, and Marathi."""
    def __init__(
        self,
        query: str,
        language: str = "all",
        label: Optional[str] = "balanced",
        target_count: int = 100,
        date_mode: str = "both",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_types: Optional[List[str]] = None,
        max_concurrent_sources: int = 10,
        max_concurrent_requests: int = 20,
    ):
        self.query = query
        self.language = language.lower().strip() if language else "all"
        self.label = label
        self.target_count = target_count
        self.date_mode = date_mode
        self.start_date = start_date
        self.end_date = end_date
        self.source_types = source_types or ["government", "news", "fact_check", "legal", "research", "archive"]
        self.max_concurrent_sources = max_concurrent_sources
        self.max_concurrent_requests = max_concurrent_requests


class ScraperService:
    """
    Multilingual scraper orchestration engine for the integrated IndicClaim pipeline.
    Reliably crawls English, Tamil, Hindi, and Marathi with language-isolated discovery,
    Unicode integrity, concurrent worker pools, and automated quality validation.
    """

    def __init__(
        self,
        dataset_manager: Optional[DatasetManager] = None,
        evidence_manager: Optional[EvidenceManager] = None,
        source_manager: Optional[SourceManager] = None,
        review_manager: Optional[ReviewManager] = None
    ):
        self.dataset_mgr = dataset_manager or DatasetManager()
        self.evidence_mgr = evidence_manager or EvidenceManager()
        self.source_mgr = source_manager or SourceManager()
        self.review_mgr = review_manager or ReviewManager()

        self.lock = threading.Lock()
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self.current_thread: Optional[threading.Thread] = None

        # State tracking & live telemetry
        self.task_id: Optional[str] = None
        self.current_query: Optional[str] = None
        self.query_intent: Optional[QueryIntent] = None
        self.current_language: str = "all"
        self.target_count: int = 0
        self.collected_count: int = 0
        self.supports_count: int = 0
        self.refutes_count: int = 0
        self.rejected_count: int = 0
        self.current_action: str = "Idle"
        
        # Multilingual Breakdown Counters
        self.lang_counts: Dict[str, int] = {"en": 0, "ta": 0, "hi": 0, "mr": 0}
        self.lang_rejected: Dict[str, int] = {"en": 0, "ta": 0, "hi": 0, "mr": 0}
        self.language_statuses: Dict[str, str] = {"en": "IDLE", "ta": "IDLE", "hi": "IDLE", "mr": "IDLE"}
        self.language_errors: Dict[str, List[str]] = {"en": [], "ta": [], "hi": [], "mr": []}

        # Two-Stage Funnel Metrics
        self.urls_discovered: int = 0
        self.stage1_passed: int = 0
        self.stage1_rejected: int = 0
        self.urls_crawled: int = 0
        self.stage2_passed: int = 0
        self.stage2_rejected: int = 0
        self.sources_active: int = 0
        self.claims_extracted: int = 0
        self.evidence_candidates: int = 0
        self.valid_supports: int = 0
        self.valid_refutes: int = 0
        self.duplicates_removed: int = 0
        self.saved_records: int = 0
        self.rejection_diagnostics: List[Dict[str, Any]] = []
        
        # Telemetry & Diagnostics
        self.last_progress_time: float = time.time()
        self.last_error: Optional[str] = None
        self.timed_out_tasks: int = 0
        self.failed_tasks: int = 0
        self.worker_health: Dict[str, str] = {}
        self.queue_sizes: Dict[str, int] = {}
        
        # In-memory shared article pool for fast local evidence cross-matching
        self._article_pool: List[Dict[str, Any]] = []
        self._pool_lock = asyncio.Lock()

        self.recent_items: List[Dict[str, Any]] = []
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.logs: List[Dict[str, Any]] = []
        self.max_logs: int = 200

        # Memory buffer for fast batch writing
        self._dataset_buffer: List[Dict[str, Any]] = []
        self._evidence_buffer: List[str] = []
        self._buffer_lock = threading.Lock()
        self.batch_size = 5

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            progress = (self.collected_count / self.target_count * 100.0) if self.target_count > 0 else 0.0
            return {
                "is_running": self.is_running,
                "is_paused": self.is_paused,
                "task_id": self.task_id,
                "query": self.current_query,
                "query_intent": self.query_intent.model_dump() if self.query_intent else None,
                "language": self.current_language,
                "target_count": self.target_count,
                "collected_count": self.collected_count,
                "supports_count": self.supports_count,
                "refutes_count": self.refutes_count,
                "rejected_count": self.rejected_count,
                "progress_pct": round(progress, 1),
                "current_action": self.current_action,
                "language_counts": dict(self.lang_counts),
                "language_rejected": dict(self.lang_rejected),
                "language_statuses": dict(self.language_statuses),
                "language_errors": dict(self.language_errors),
                "funnel": {
                    "query_id": self.query_intent.query_id if self.query_intent else "",
                    "original_query": self.current_query,
                    "discovered_count": self.urls_discovered,
                    "potentially_relevant_stage1": self.stage1_passed,
                    "stage1_rejected": self.stage1_rejected,
                    "downloaded_count": self.urls_crawled,
                    "relevant_stage2": self.stage2_passed,
                    "stage2_rejected": self.stage2_rejected,
                    "duplicates_removed": self.duplicates_removed,
                    "verified_count": self.collected_count,
                    "training_eligible_count": self.saved_records
                },
                "sources_active": self.sources_active,
                "urls_discovered": self.urls_discovered,
                "urls_crawled": self.urls_crawled,
                "claims_extracted": self.claims_extracted,
                "evidence_candidates": self.evidence_candidates,
                "valid_supports": self.valid_supports,
                "valid_refutes": self.valid_refutes,
                "duplicates_removed": self.duplicates_removed,
                "saved_records": self.saved_records,
                "recent_items": list(self.recent_items[-10:]),
                "rejection_diagnostics": list(self.rejection_diagnostics[-15:]),
                "logs": [{"timestamp": l.get("timestamp", ""), "level": l.get("level", ""), "message": l.get("message", "")} for l in self.logs[-50:]],
                "start_time": self.start_time,
                "end_time": self.end_time
            }

    def get_diagnostics(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "worker_health": dict(self.worker_health),
                "queues": dict(self.queue_sizes),
                "language_statuses": dict(self.language_statuses),
                "timed_out_tasks": self.timed_out_tasks,
                "failed_tasks": self.failed_tasks,
                "last_error": self.last_error,
                "article_pool_size": len(self._article_pool),
            }

    def log(self, level: str, message: str):
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message
        }
        with self.lock:
            self.logs.append(entry)
            if len(self.logs) > self.max_logs:
                self.logs = self.logs[-self.max_logs:]

    def start_scraping(self, request: CrawlRequest) -> Dict[str, Any]:
        with self.lock:
            if self.is_running:
                return {"status": "error", "message": "Scraper is already running"}

        self._reset_state(request)

        self.current_thread = threading.Thread(
            target=self._run_pipeline_thread,
            args=(request,),
            daemon=True,
            name="ScraperPipeline"
        )
        self.current_thread.start()
        self.log("INFO", f"[CRAWLER] Started multilingual pipeline for topic: '{request.query}' (lang: {request.language}, target: {request.target_count})")
        return {"status": "success", "task_id": self.task_id, "message": f"Scraping started for '{request.query}' ({request.language})"}

    def pause_scraping(self) -> Dict[str, Any]:
        with self.lock:
            if not self.is_running:
                return {"status": "error", "message": "Scraper is not running"}
            self.is_paused = True
            self.current_action = "Paused"
        return {"status": "success", "message": "Scraping paused"}

    def resume_scraping(self) -> Dict[str, Any]:
        with self.lock:
            if not self.is_running:
                return {"status": "error", "message": "Scraper is not running"}
            self.is_paused = False
            self.current_action = "Resuming..."
        return {"status": "success", "message": "Scraping resumed"}

    def stop_scraping(self) -> Dict[str, Any]:
        with self.lock:
            if not self.is_running:
                return {"status": "error", "message": "Scraper is not running"}
            self.stop_requested = True
            self.current_action = "Stopping..."
        return {"status": "success", "message": "Stop signal sent"}

    def _reset_state(self, request: CrawlRequest):
        with self.lock:
            self.is_running = True
            self.is_paused = False
            self.stop_requested = False
            self.task_id = str(uuid.uuid4())[:8]
            self.current_query = request.query
            self.current_language = request.language
            self.target_count = request.target_count
            self.collected_count = 0
            self.supports_count = 0
            self.refutes_count = 0
            self.rejected_count = 0
            self.current_action = "Analyzing Query Intent..."
            self.lang_counts = {"en": 0, "ta": 0, "hi": 0, "mr": 0}
            self.lang_rejected = {"en": 0, "ta": 0, "hi": 0, "mr": 0}
            self.language_statuses = {"en": "PENDING", "ta": "PENDING", "hi": "PENDING", "mr": "PENDING"} if request.language in ["all", "multi", "multilingual"] else {request.language: "PENDING"}
            self.language_errors = {"en": [], "ta": [], "hi": [], "mr": []}
            self.sources_active = 0
            self.urls_discovered = 0
            self.stage1_passed = 0
            self.stage1_rejected = 0
            self.urls_crawled = 0
            self.stage2_passed = 0
            self.stage2_rejected = 0
            self.claims_extracted = 0
            self.evidence_candidates = 0
            self.valid_supports = 0
            self.valid_refutes = 0
            self.duplicates_removed = 0
            self.saved_records = 0
            self.rejection_diagnostics = []
            self.last_error = None
            self.timed_out_tasks = 0
            self.failed_tasks = 0
            self.worker_health = {}
            self.queue_sizes = {}
            self._article_pool = []
            self.recent_items = []
            self.logs = []
            self.start_time = datetime.now().isoformat()
            self.end_time = None
            self._dataset_buffer = []
            self._evidence_buffer = []
            self.last_progress_time = time.time()

            # Analyze and decompose query intent
            target_langs = ["en", "ta", "hi", "mr"] if request.language in ["all", "multi", "multilingual"] else [request.language]
            self.query_intent = QueryIntentAnalyzer.analyze_query(request.query, target_languages=target_langs)

    def _run_pipeline_thread(self, request: CrawlRequest):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._pipeline_main(request))
        except Exception as e:
            self.log("ERROR", f"[CRAWLER] Pipeline thread error: {e}")
            self.last_error = str(e)
        finally:
            with self.lock:
                self.is_running = False
                self.end_time = datetime.now().isoformat()
                self.current_action = f"Completed — {self.collected_count} items collected"
            self.log("INFO", f"[CRAWLER] Multilingual pipeline finished. Total: {self.collected_count} (EN:{self.lang_counts.get('en',0)}, TA:{self.lang_counts.get('ta',0)}, HI:{self.lang_counts.get('hi',0)}, MR:{self.lang_counts.get('mr',0)})")

    async def _pipeline_main(self, request: CrawlRequest):
        crawler = AsyncCrawler(
            max_concurrent_requests=request.max_concurrent_requests,
            timeout=4.5
        )
        search_engine = AsyncSearchEngine(crawler)

        # Load existing items for duplicate detection
        existing_items = self.dataset_mgr.load_all()
        dup_detector = DuplicateDetector(existing_items)
        quality_checker = QualityChecker(
            min_claim_length=20,
            max_claim_length=450,
            min_evidence_length=40,
            max_evidence_length=1800,
            min_relevance_score=0.22,
            min_confidence_score=0.60
        )

        url_queue = asyncio.Queue(maxsize=400)
        article_queue = asyncio.Queue(maxsize=150)
        claim_queue = asyncio.Queue(maxsize=300)
        evidence_queue = asyncio.Queue(maxsize=300)
        save_queue = asyncio.Queue(maxsize=150)

        source_types = request.source_types or ["government", "news", "fact_check", "legal", "research", "archive"]
        target_langs = ["en", "ta", "hi", "mr"] if request.language in ["all", "multi", "multilingual"] else [request.language]

        try:
            # PHASE 1: Query-Driven Multilingual URL Discovery with Stage 1 Relevance Filter
            self.current_action = f"Phase 1: Query Discovery for '{self.query_intent.topic}' ({self.query_intent.year or 'All Years'})..."
            self.log("INFO", f"[CRAWLER] Query Intent decomposed: Topic='{self.query_intent.topic}', Event='{self.query_intent.event}', Year={self.query_intent.year}, Langs={target_langs}")

            accepted_by_lang: Dict[str, List[Dict[str, Any]]] = {l: [] for l in target_langs}

            async def _discover_lang(lang: str):
                with self.lock:
                    self.language_statuses[lang] = "DISCOVERING"
                try:
                    accepted_results, rejected_results = await search_engine.search_by_intent(
                        intent=self.query_intent,
                        language=lang,
                        max_results=18,
                        min_stage1_threshold=0.40
                    )
                    with self.lock:
                        self.sources_active += 1
                        self.urls_discovered += (len(accepted_results) + len(rejected_results))
                        self.stage1_passed += len(accepted_results)
                        self.stage1_rejected += len(rejected_results)
                        for rej in rejected_results[:3]:
                            self.rejection_diagnostics.append(rej.get("stage1_diagnostics", {}))
                    accepted_by_lang[lang] = accepted_results
                    self.log("INFO", f"[CRAWLER] [{lang.upper()}] Stage 1 Search Filter: {len(accepted_results)} potentially relevant passed, {len(rejected_results)} rejected")
                except Exception as e:
                    with self.lock:
                        self.language_errors[lang].append(str(e))
                    self.log("WARN", f"[CRAWLER] [{lang.upper()}] Intent search error: {e}")
                with self.lock:
                    self.language_statuses[lang] = "CRAWLING" if len(accepted_by_lang[lang]) > 0 else "PARTIAL"

            await asyncio.gather(*[_discover_lang(l) for l in target_langs])

            # Round-robin interleaved insertion into URL queue to balance worker load evenly
            max_len = max([len(items) for items in accepted_by_lang.values()] or [0])
            for i in range(max_len):
                for lang in target_langs:
                    if i < len(accepted_by_lang[lang]):
                        item = accepted_by_lang[lang][i]
                        item["expected_language"] = lang
                        if not url_queue.full():
                            await url_queue.put(item)

            self.log("INFO", f"[CRAWLER] Discovered {self.urls_discovered} candidate URLs | Stage 1 Passed: {self.stage1_passed} | Stage 1 Rejected: {self.stage1_rejected}")

            # PHASE 2: Launch concurrent workers
            self.current_action = "Phase 2: Crawling, Deep Content Relevance & Extraction..."

            workers = [
                # Fetcher workers
                *[asyncio.create_task(self._fetcher_worker(crawler, url_queue, article_queue, f"Fetcher-{i}"))
                  for i in range(min(8, request.max_concurrent_requests))],
                # Extractor workers
                *[asyncio.create_task(self._extractor_worker(article_queue, claim_queue, f"Extractor-{i}"))
                  for i in range(4)],
                # Evidence matcher workers
                *[asyncio.create_task(self._evidence_worker(
                    claim_queue, evidence_queue, dup_detector, quality_checker, f"EvidenceWorker-{i}"))
                  for i in range(4)],
                # Save worker
                asyncio.create_task(self._save_worker(
                    evidence_queue, save_queue, request, dup_detector)),
                # Watchdog
                asyncio.create_task(self._watchdog_monitor(url_queue, article_queue, claim_queue, evidence_queue, save_queue)),
            ]

            # Wait for URL queue to drain
            await url_queue.join()
            
            # Allow remaining workers to process
            deadline = time.time() + 35.0
            while time.time() < deadline and self.collected_count < request.target_count:
                if self.stop_requested:
                    break
                all_empty = (article_queue.empty() and claim_queue.empty() and evidence_queue.empty() and save_queue.empty())
                if all_empty:
                    break
                await asyncio.sleep(0.5)

            self.stop_requested = True
            for w in workers:
                w.cancel()
            await asyncio.gather(*workers, return_exceptions=True)

            # Update final language statuses
            with self.lock:
                for lang in target_langs:
                    if self.lang_counts.get(lang, 0) > 0:
                        self.language_statuses[lang] = "SUCCESS"
                    elif self.language_statuses.get(lang) == "CRAWLING":
                        self.language_statuses[lang] = "PARTIAL"

        except Exception as e:
            self.log("ERROR", f"[CRAWLER] Pipeline error: {e}")
            self.last_error = str(e)
        finally:
            await crawler.close()
            self._flush_buffers()
            self.log("INFO", f"[CRAWLER] Final Funnel: Discovered={self.urls_discovered}, Stage1 Passed={self.stage1_passed}, Downloaded={self.urls_crawled}, Stage2 Relevant={self.stage2_passed}, Verified={self.collected_count}")

            # Check Automatic Retraining Trigger if new verified records collected
            if self.saved_records > 0:
                try:
                    from app.services.training_service import TrainingService
                    ts = TrainingService(dataset_manager=self.dataset_mgr)
                    ts.increment_new_examples(self.saved_records)
                    trig = ts.get_trigger_status()
                    self.log("INFO", f"[AUTO-TRAIN] New examples added: {self.saved_records}. Total un-trained: {trig.get('new_examples_since_last_training')}/{trig.get('threshold')}")
                    if trig.get("auto_train_enabled") and trig.get("is_threshold_reached") and not trig.get("is_training_locked"):
                        self.log("INFO", "[AUTO-TRAIN] Retrain threshold met! Initiating background MuRIL model training...")
                        threading.Thread(target=ts.train, kwargs={"epochs": 2, "batch_size": 4}, daemon=True).start()
                except Exception as ex:
                    self.log("WARN", f"[AUTO-TRAIN] Error checking retraining trigger: {ex}")

    # =========================================================================
    # FETCHER WORKERS (WITH STAGE 2 CONTENT RELEVANCE VALIDATION)
    # =========================================================================

    async def _fetcher_worker(self, crawler: AsyncCrawler, url_queue: asyncio.Queue, article_queue: asyncio.Queue, worker_name: str):
        self.worker_health[worker_name] = "Active"
        while not self.stop_requested:
            try:
                while self.is_paused and not self.stop_requested:
                    await asyncio.sleep(0.2)

                try:
                    item = await asyncio.wait_for(url_queue.get(), timeout=3.0)
                except asyncio.TimeoutError:
                    if url_queue.empty():
                        break
                    continue

                url = item.get("url", "")
                exp_lang = item.get("expected_language", "en")
                if not url or crawler.is_url_crawled(url):
                    url_queue.task_done()
                    continue

                doc = await crawler.fetch_and_extract(
                    url=url,
                    source_type=item.get("source_type", "news"),
                    source_name=item.get("source", "Web")
                )

                with self.lock:
                    self.urls_crawled += 1

                if doc and doc.get("paragraphs"):
                    full_text = doc.get("text", "") or " ".join(doc.get("paragraphs", []))
                    
                    # Language detection on document text
                    doc_lang_res = LanguageDetector.detect_language(f"{doc.get('title', '')} {full_text[:500]}")
                    doc_lang = doc_lang_res["language"]
                    doc["language"] = doc_lang
                    doc["expected_language"] = exp_lang

                    # Stage 2: Deep Article Content & Temporal Relevance Validation
                    if self.query_intent:
                        is_rel, stage2_diag = TopicRelevanceFilter.evaluate_stage2_content(
                            intent=self.query_intent,
                            title=doc.get("title", ""),
                            full_text=full_text,
                            pub_date=doc.get("published_date", "") or item.get("published_date", ""),
                            url=url,
                            source_name=doc.get("source_name", ""),
                            lang=doc_lang,
                            min_threshold=0.50
                        )
                        doc["stage2_diagnostics"] = stage2_diag.model_dump()
                        doc["relevance_score"] = stage2_diag.relevance_score
                        doc["query_id"] = self.query_intent.query_id

                        if not is_rel:
                            with self.lock:
                                self.stage2_rejected += 1
                                self.rejected_count += 1
                                self.lang_rejected[doc_lang] = self.lang_rejected.get(doc_lang, 0) + 1
                                if len(self.rejection_diagnostics) < 30:
                                    self.rejection_diagnostics.append(stage2_diag.model_dump())
                            self.log("INFO", f"[FETCHER] Stage 2 Rejected ({stage2_diag.rejection_reason}): {doc.get('title', url)[:60]}")
                            url_queue.task_done()
                            continue
                        else:
                            with self.lock:
                                self.stage2_passed += 1

                    async with self._pool_lock:
                        self._article_pool.append(doc)
                    if not article_queue.full():
                        await article_queue.put(doc)
                    self.log("SUCCESS", f"[FETCHER] [{doc['language'].upper()}] Stage 2 Relevant (Score: {doc.get('relevance_score', 1.0):.2f}): {doc.get('title', url)[:60]}")

                url_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception:
                self.failed_tasks += 1
                await asyncio.sleep(0.1)

        self.worker_health[worker_name] = "Done"

    # =========================================================================
    # EXTRACTOR WORKERS
    # =========================================================================

    async def _extractor_worker(self, article_queue: asyncio.Queue, claim_queue: asyncio.Queue, worker_name: str):
        self.worker_health[worker_name] = "Active"
        while not self.stop_requested:
            try:
                while self.is_paused and not self.stop_requested:
                    await asyncio.sleep(0.2)

                try:
                    doc = await asyncio.wait_for(article_queue.get(), timeout=3.0)
                except asyncio.TimeoutError:
                    if not self.is_running or article_queue.empty():
                        break
                    continue

                title = doc.get("title", "")
                paragraphs = doc.get("paragraphs", [])
                source_type = doc.get("source_type", "news")
                exp_lang = doc.get("expected_language", "en")

                claims = await asyncio.to_thread(
                    ClaimExtractor.extract_claims_from_text,
                    doc.get("text", ""),
                    title=title,
                    source_type=source_type
                )

                for claim in claims:
                    claim_text = claim["claim_text"]
                    claim_lang = claim.get("language") or LanguageDetector.detect_language(claim_text)["language"]

                    # Ensure topic alignment for extracted claim
                    if self.query_intent:
                        topic_kws = (
                            self.query_intent.topic_keywords.get(claim_lang, []) +
                            self.query_intent.topic_keywords.get(exp_lang, []) +
                            self.query_intent.topic_keywords.get("en", [])
                        )
                        combined_claim_ctx = f"{title} {claim_text}".lower()
                        has_topic_match = any(kw.lower() in combined_claim_ctx for kw in topic_kws if kw)
                        if not has_topic_match:
                            is_rel, _, _ = TopicRelevanceFilter.is_relevant(
                                self.query_intent.original_query,
                                claim_text,
                                snippet=title,
                                min_keyword_overlap=0.10
                            )
                            if not is_rel:
                                continue
                    else:
                        is_rel, _, _ = TopicRelevanceFilter.is_relevant(
                            self.current_query,
                            claim_text,
                            snippet=title,
                            min_keyword_overlap=0.15
                        )
                        if not is_rel:
                            continue

                    with self.lock:
                        self.claims_extracted += 1

                    claim_data = {
                        "claim_text": claim_text,
                        "language": claim_lang,
                        "expected_language": exp_lang,
                        "confidence": claim.get("confidence", 0.5),
                        "source_type": source_type,
                        "article_paragraphs": paragraphs,
                        "article_title": title,
                        "article_url": doc.get("url", ""),
                        "source": doc.get("source", "Web"),
                        "query_id": doc.get("query_id"),
                        "relevance_score": doc.get("relevance_score", 1.0),
                        "stage2_diagnostics": doc.get("stage2_diagnostics", {})
                    }
                    if not claim_queue.full():
                        await claim_queue.put(claim_data)

                article_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.05)

        self.worker_health[worker_name] = "Done"

    # =========================================================================
    # EVIDENCE MATCHING & VERIFICATION WORKERS
    # =========================================================================

    async def _evidence_worker(
        self,
        claim_queue: asyncio.Queue,
        evidence_queue: asyncio.Queue,
        dup_detector: DuplicateDetector,
        quality_checker: QualityChecker,
        worker_name: str
    ):
        self.worker_health[worker_name] = "Active"
        while not self.stop_requested:
            try:
                while self.is_paused and not self.stop_requested:
                    await asyncio.sleep(0.2)

                try:
                    claim_data = await asyncio.wait_for(claim_queue.get(), timeout=3.0)
                except asyncio.TimeoutError:
                    if not self.is_running or claim_queue.empty():
                        break
                    continue

                claim_text = claim_data["claim_text"]
                paragraphs = claim_data.get("article_paragraphs", [])
                claim_lang = claim_data.get("language", "en")

                # Extract evidence candidates
                ev_candidates = await asyncio.to_thread(
                    EvidenceExtractor.extract_evidence_candidates,
                    paragraphs, claim_text
                )

                with self.lock:
                    self.evidence_candidates += len(ev_candidates)

                # Also check shared article pool for matching language
                async with self._pool_lock:
                    pool_copy = [d for d in self._article_pool[-50:] if d.get("language") == claim_lang]

                for pool_doc in pool_copy:
                    if pool_doc.get("url") == claim_data.get("article_url"):
                        continue
                    pool_paras = pool_doc.get("paragraphs", [])
                    if pool_paras:
                        cross_ev = await asyncio.to_thread(
                            EvidenceExtractor.extract_evidence_candidates,
                            pool_paras, claim_text, 40, 900
                        )
                        ev_candidates.extend(cross_ev)

                # Score and validate each candidate
                for ev_cand in ev_candidates[:6]:
                    evidence_text = ev_cand.get("evidence_text", "")
                    if not evidence_text:
                        continue

                    match_result = await asyncio.to_thread(
                        CandidateMatcher.compute_match_score, claim_text, evidence_text
                    )
                    match_score = match_result.get("score", 0.0)

                    if not match_result.get("is_relevant", False):
                        continue

                    label, confidence, reason = await asyncio.to_thread(
                        LabelGenerator.generate_label,
                        claim_text, evidence_text, match_score,
                        claim_data.get("source_type")
                    )

                    # Check for duplicates
                    is_dup, dup_reason = dup_detector.is_duplicate(
                        claim_text, evidence_text, language=claim_lang
                    )

                    # Validate quality
                    is_valid, q_reason, diag = quality_checker.validate(
                        claim=claim_text,
                        evidence=evidence_text,
                        label=label,
                        match_score=match_score,
                        confidence=confidence,
                        is_duplicate=is_dup,
                        duplicate_reason=dup_reason,
                        expected_language=claim_data.get("expected_language")
                    )

                    if is_valid and label in ["SUPPORTS", "REFUTES"]:
                        event_id = None
                        if self.query_intent:
                            event_id = f"{self.query_intent.topic[:8].upper()}-{self.query_intent.year or 'GEN'}-{abs(hash(claim_data.get('article_title', ''))) % 1000:03d}"

                        verified_item = {
                            "Text": claim_text,
                            "Evidence": evidence_text,
                            "Label": label,
                            "Language": claim_lang,
                            "Source": claim_data.get("source", "Web"),
                            "SourceUrl": claim_data.get("article_url", ""),
                            "confidence": confidence,
                            "match_score": match_score,
                            "reason": reason,
                            "query_id": claim_data.get("query_id"),
                            "canonical_query": self.current_query,
                            "relevance_score": claim_data.get("relevance_score", 1.0),
                            "event_id": event_id
                        }
                        if not evidence_queue.full():
                            await evidence_queue.put(verified_item)
                        dup_detector.register_item(verified_item)
                        break  # One verified evidence per claim
                    else:
                        with self.lock:
                            self.rejected_count += 1
                            self.lang_rejected[claim_lang] = self.lang_rejected.get(claim_lang, 0) + 1
                            if is_dup:
                                self.duplicates_removed += 1
                        await asyncio.to_thread(
                            self.review_mgr.add_rejected,
                            claim_text, evidence_text, q_reason,
                            confidence, label,
                            metadata={"language": claim_lang, "source": claim_data.get("source", "")}
                        )

                claim_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.05)

        self.worker_health[worker_name] = "Done"

    # =========================================================================
    # SAVE WORKER
    # =========================================================================

    async def _save_worker(
        self,
        evidence_queue: asyncio.Queue,
        save_queue: asyncio.Queue,
        request: CrawlRequest,
        dup_detector: DuplicateDetector
    ):
        self.worker_health["SaveWorker"] = "Active"
        while not self.stop_requested or not evidence_queue.empty():
            try:
                while self.is_paused and not self.stop_requested:
                    await asyncio.sleep(0.2)

                try:
                    item = await asyncio.wait_for(evidence_queue.get(), timeout=2.0)
                except asyncio.TimeoutError:
                    self._flush_buffer_if_needed()
                    if not self.is_running and evidence_queue.empty():
                        break
                    continue

                is_multi = request.language in ["all", "multi", "multilingual"]
                lang = item.get("Language", "en")
                per_lang_target = max(3, request.target_count // 4)

                # Multilingual fairness: if this language has plenty and we still need other languages, throttle it
                if is_multi and self.lang_counts.get(lang, 0) >= (per_lang_target + 3) and self.collected_count >= (request.target_count * 0.7):
                    # Check if any other language is at 0
                    if any(self.lang_counts.get(l, 0) == 0 for l in ["en", "ta", "hi", "mr"]):
                        evidence_queue.task_done()
                        continue

                if self.collected_count >= request.target_count:
                    # Allow non-represented languages a few extra slots
                    if is_multi and self.lang_counts.get(lang, 0) < per_lang_target and self.collected_count < (request.target_count * 1.4):
                        pass
                    else:
                        evidence_queue.task_done()
                        continue

                with self._buffer_lock:
                    self._dataset_buffer.append({
                        "Text": item["Text"],
                        "Evidence": item["Evidence"],
                        "Label": item["Label"],
                        "Language": lang,
                        "Source": item.get("Source", "Web"),
                        "SourceUrl": item.get("SourceUrl", ""),
                        "query_id": item.get("query_id"),
                        "canonical_query": item.get("canonical_query"),
                        "relevance_score": item.get("relevance_score", 1.0),
                        "event_id": item.get("event_id")
                    })
                    self._evidence_buffer.append(item["Evidence"])

                with self.lock:
                    self.collected_count += 1
                    self.saved_records += 1
                    self.lang_counts[lang] = self.lang_counts.get(lang, 0) + 1
                    if item["Label"] == "SUPPORTS":
                        self.supports_count += 1
                        self.valid_supports += 1
                    else:
                        self.refutes_count += 1
                        self.valid_refutes += 1

                    self.recent_items.append({
                        "ID": f"S1/{self.collected_count:06d}",
                        "Text": item["Text"],
                        "Evidence": item["Evidence"],
                        "Label": item["Label"],
                        "Language": lang
                    })
                    if len(self.recent_items) > 25:
                        self.recent_items.pop(0)
                    self.last_progress_time = time.time()

                self.log("SUCCESS", f"[SAVE] [{lang.upper()}] [{item['Label']}] Claim: '{item['Text'][:50]}...'")
                evidence_queue.task_done()
                self._flush_buffer_if_needed()

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.05)

        self._flush_buffers()
        self.worker_health["SaveWorker"] = "Done"

    # =========================================================================
    # WATCHDOG & HEARTBEAT SYSTEM
    # =========================================================================

    async def _watchdog_monitor(
        self,
        url_q: asyncio.Queue,
        art_q: asyncio.Queue,
        claim_q: asyncio.Queue,
        ev_q: asyncio.Queue,
        save_q: asyncio.Queue
    ):
        while not self.stop_requested and self.is_running:
            try:
                await asyncio.sleep(3.0)
                
                with self.lock:
                    self.queue_sizes = {
                        "url_queue": url_q.qsize(),
                        "article_queue": art_q.qsize(),
                        "claim_queue": claim_q.qsize(),
                        "evidence_queue": ev_q.qsize(),
                        "save_queue": save_q.qsize()
                    }
                    time_since_progress = time.time() - self.last_progress_time

                if time_since_progress > 25.0 and self.collected_count < self.target_count:
                    self.log("WARN", f"[WATCHDOG] No progress for {int(time_since_progress)}s. Recovering queues...")
                    with self.lock:
                        self.last_progress_time = time.time()

            except asyncio.CancelledError:
                break
            except Exception:
                pass

    def _flush_buffer_if_needed(self):
        with self._buffer_lock:
            if len(self._dataset_buffer) >= self.batch_size:
                ds_items = list(self._dataset_buffer)
                ev_items = list(self._evidence_buffer)
                self._dataset_buffer.clear()
                self._evidence_buffer.clear()
            else:
                return

        if ds_items:
            self.dataset_mgr.add_items_batch(ds_items)
        if ev_items:
            self.evidence_mgr.add_evidence_batch(ev_items)

    def _flush_buffers(self):
        with self._buffer_lock:
            ds_items = list(self._dataset_buffer)
            ev_items = list(self._evidence_buffer)
            self._dataset_buffer.clear()
            self._evidence_buffer.clear()

        if ds_items:
            self.dataset_mgr.add_items_batch(ds_items)
        if ev_items:
            self.evidence_mgr.add_evidence_batch(ev_items)
