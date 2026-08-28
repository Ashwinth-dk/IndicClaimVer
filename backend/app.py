import os
import sys
import io
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from backend.config import API_HOST, API_PORT

from backend.data_pipeline import normalize_text, get_dataset_statistics, load_json_records
from backend.retriever import get_retriever
from backend.sentence_selector import get_sentence_selector
from backend.veracity_model import get_veracity_model
from backend.scraper.crawler import get_crawler
from backend.scraper.live_search import search_live_web_evidence
from backend.trainer import get_trainer

app = FastAPI(
    title="VeriClaim-AI API",
    description="Multi-Lingual Fact Verification & Evidence Web Crawling Engine",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Models
class VerifyRequest(BaseModel):
    claim: str
    evidence: Optional[str] = None
    mode: str = "local"  # "local", "live_web", or "hybrid"
    top_k: int = 3

class CrawlRequest(BaseModel):
    query: Optional[str] = None
    topics: Optional[List[str]] = None
    max_per_topic: int = 15

class TrainRequest(BaseModel):
    include_crawled: bool = True
    epochs: int = 5
    batch_size: int = 16
    learning_rate: float = 2e-5

# Global background task states
crawler_state = {"status": "idle", "message": "", "progress": 0}
training_state = {"status": "idle", "message": "", "progress": 0}

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "VeriClaim-AI"}

@app.get("/api/presets")
def get_presets():
    """Returns curated multi-lingual test claims for instant testing."""
    return [
        {
            "language": "Hindi",
            "claim": "ममता बनर्जी ने किसी भी मंत्री को पद से नहीं हटाया, बल्कि सभी को उनके वर्तमान दायित्वों पर बने रहने का निर्देश दिया।",
            "expected_veracity": "REFUTES",
            "topic": "Politics"
        },
        {
            "language": "Bengali",
            "claim": "প্রতি ঘণ্টায় চাই হোম কোয়ারেন্টাইনদের ভিডিও! নয়া ঘোষণা কর্ণাটক সরকারের",
            "expected_veracity": "REFUTES",
            "topic": "COVID Health"
        },
        {
            "language": "Bengali",
            "claim": "করোনা সংক্রমণের আতঙ্ক, ভিনরাজ্যে কর্মরত যুবককে গ্রামে ঢুকতে বাধা প্রতিবেশীদের",
            "expected_veracity": "SUPPORTS",
            "topic": "COVID News"
        },
        {
            "language": "Hindi",
            "claim": "जम्मू-कश्मीर में हालात सुधारने और शांति वापस लाने के लिए कांग्रेस ने नरेंद्र मोदी से पूछे सवाल",
            "expected_veracity": "SUPPORTS",
            "topic": "Politics"
        },
        {
            "language": "English",
            "claim": "Ensure adequate buffer stock of medical oxygen: Centre to states",
            "expected_veracity": "SUPPORTS",
            "topic": "Healthcare"
        },
        {
            "language": "English",
            "claim": "Nine out of 18 Aam Aadmi Party candidates in Delhi are crorepatis",
            "expected_veracity": "SUPPORTS",
            "topic": "Elections"
        },
        {
            "language": "Hindi",
            "claim": "विश्व बैंक ने कहा- यूक्रेन युद्ध का गरीबों पर असर नहीं पड़ा, हालात सिर्फ कोरोना महामारी से बिगड़े।",
            "expected_veracity": "REFUTES",
            "topic": "Economy"
        },
        {
            "language": "English",
            "claim": "Delhi will report more than 5,000 cases today: Satyendar Jain",
            "expected_veracity": "REFUTES",
            "topic": "COVID Health"
        }
    ]

@app.post("/api/verify")
def verify_claim(req: VerifyRequest):
    """
    Main claim verification pipeline:
    1. Retrieves evidence (from Local Pool or Live Web Scraper).
    2. Extracts salient sentence rationale.
    3. Infers veracity (SUPPORTS / REFUTES / NOT ENOUGH INFO).
    """
    claim = normalize_text(req.claim)
    if not claim:
        raise HTTPException(status_code=400, detail="Claim cannot be empty.")

    retriever = get_retriever()
    selector = get_sentence_selector()
    model = get_veracity_model()

    retrieved_passages: List[Dict[str, Any]] = []

    # 1. Custom evidence provided
    if req.evidence and len(normalize_text(req.evidence)) > 15:
        primary_evidence = normalize_text(req.evidence)
        retrieved_passages.append({
            "id": "CUSTOM_INPUT",
            "evidence": primary_evidence,
            "score": 1.0,
            "source": "User Provided",
            "retrieval_mode": "user_input"
        })
    elif req.mode == "live_web":
        # 2. Live Web Scraper mode
        live_results = search_live_web_evidence(claim, max_results=req.top_k)
        retrieved_passages.extend(live_results)
        primary_evidence = live_results[0]["evidence"] if live_results else ""
    elif req.mode == "hybrid":
        # 3. Hybrid (Local + Live Web)
        local_results = retriever.retrieve(claim, top_k=req.top_k)
        live_results = search_live_web_evidence(claim, max_results=2)
        retrieved_passages.extend(live_results)
        retrieved_passages.extend(local_results)
        primary_evidence = retrieved_passages[0]["evidence"] if retrieved_passages else ""
    else:
        # 4. Local Evidence Pool with intelligent Web Fallback if pool lacks subject
        local_results = retriever.retrieve(claim, top_k=req.top_k)
        
        # Check if local pool had strong match
        if local_results and local_results[0]["score"] >= 0.28:
            retrieved_passages.extend(local_results)
            primary_evidence = local_results[0]["evidence"]
        else:
            # Fallback to live web knowledge search if local pool has no matching documents
            live_results = search_live_web_evidence(claim, max_results=req.top_k)
            if live_results:
                retrieved_passages.extend(live_results)
                primary_evidence = live_results[0]["evidence"]
            elif local_results:
                retrieved_passages.extend(local_results)
                primary_evidence = local_results[0]["evidence"]
            else:
                primary_evidence = ""


    # 2. Sentence Selection & Salience Ranking
    salient_sentences = []
    if primary_evidence:
        salient_sentences = selector.select_salient_sentences(claim, primary_evidence, top_k=2)

    decisive_evidence = salient_sentences[0]["sentence"] if salient_sentences else primary_evidence

    # 3. Veracity Prediction
    prediction = model.predict(claim, decisive_evidence)

    return {
        "claim": claim,
        "mode": req.mode,
        "veracity": prediction["veracity"],
        "display_veracity": prediction["display_veracity"],
        "confidence": prediction["confidence"],
        "probabilities": prediction["probabilities"],
        "explanation": prediction["explanation"],
        "decisive_sentence": decisive_evidence,
        "salient_sentences": salient_sentences,
        "retrieved_passages": retrieved_passages,
        "model_source": prediction.get("model_source", "transformer")
    }

@app.post("/api/crawl")
def trigger_crawl(req: CrawlRequest, bg_tasks: BackgroundTasks):
    """Triggers background web crawling across fact-checking sites."""
    global crawler_state
    if crawler_state["status"] == "running":
        return {"status": "already_running", "message": "Crawler is currently active."}

    def crawl_job():
        global crawler_state
        from backend.scraper.dataset_scraper import DatasetScraper
        scraper = DatasetScraper()
        crawler_state["status"] = "running"
        crawler_state["progress"] = 15
        
        try:
            if req.query:
                crawler_state["message"] = f"Scraping custom topic: '{req.query}'..."
                crawler_state["progress"] = 35
                results = scraper.scrape_topic(req.query, max_items=req.max_per_topic)
                crawler_state["progress"] = 75
                total_records = scraper.save_dataset(results, append=True)
                crawler_state["progress"] = 100
                crawler_state["message"] = f"Successfully harvested and stored {len(results)} fact-checked items for '{req.query}'. Total records: {total_records}."
            else:
                crawler_state["message"] = "Harvesting multi-domain fact-checked claims..."
                crawler_state["progress"] = 25
                results = scraper.scrape_multi_domain_dataset(
                    topics=req.topics,
                    target_count=req.max_per_topic * 2
                )
                crawler_state["progress"] = 80
                total_records = scraper.save_dataset(results, append=True)
                crawler_state["progress"] = 100
                crawler_state["message"] = f"Multi-source crawl completed. Added {len(results)} verified items. Total records: {total_records}."
            
            # Refresh retriever index with new data
            get_retriever().load_corpus()
            get_retriever().build_tfidf_index()
            
            crawler_state["status"] = "completed"
        except Exception as e:
            crawler_state["status"] = "error"
            crawler_state["message"] = f"Crawler error: {e}"

    bg_tasks.add_task(crawl_job)
    return {"status": "started", "message": "Web crawling started in background."}

@app.get("/api/crawl/status")
def get_crawl_status():
    """Returns current crawler status, count of crawled items, and recent samples."""
    global crawler_state
    crawler = get_crawler()
    crawled_items = load_json_records(crawler.output_path)
    return {
        "status": crawler_state["status"],
        "message": crawler_state["message"],
        "progress": crawler_state["progress"],
        "total_crawled": len(crawled_items),
        "recent_samples": crawled_items[-10:] if crawled_items else []
    }

@app.post("/api/train")
def trigger_train(req: TrainRequest, bg_tasks: BackgroundTasks):
    """Triggers model fine-tuning with existing and newly crawled data."""
    global training_state
    if training_state["status"] == "running":
        return {"status": "already_running", "message": "Model training is currently active."}

    def train_job():
        global training_state
        trainer = get_trainer()
        training_state["status"] = "running"
        training_state["progress"] = 5
        
        def progress_cb(msg: str, pct: int):
            training_state["message"] = msg
            training_state["progress"] = pct

        try:
            metrics = trainer.train(
                include_crawled=req.include_crawled,
                epochs=req.epochs,
                batch_size=req.batch_size,
                lr=req.learning_rate,
                progress_callback=progress_cb
            )
            # Reload veracity model with newly trained weights
            get_veracity_model().load_model()
            training_state["status"] = "completed"
            training_state["metrics"] = metrics
        except Exception as e:
            training_state["status"] = "error"
            training_state["message"] = str(e)

    bg_tasks.add_task(train_job)
    return {"status": "started", "message": "Model training started in background."}

@app.get("/api/train/status")
def get_train_status():
    global training_state
    return training_state

@app.get("/api/metrics")
def get_metrics():
    """Returns dataset metrics, model evaluation scores, and confusion matrix."""
    trainer = get_trainer()
    dataset_stats = get_dataset_statistics()
    model_metrics = trainer.get_latest_metrics()
    return {
        "dataset_statistics": dataset_stats,
        "model_performance": model_metrics
    }

# Serve Frontend static assets
frontend_dir = BASE_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(frontend_dir / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host=API_HOST, port=API_PORT, reload=False)
