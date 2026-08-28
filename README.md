# IndicClaimVer

Multilingual Fact-Checking & Automated Evidence Verification for Indic and Global News Claims.

## 📌 Overview

**IndicClaimVer** is an end-to-end automated claim verification and fact-checking system. It leverages transformer-based language models (XLM-RoBERTa), hybrid lexical & neural evidence retrieval, automated continuous web crawling from reputed fact-checking portals (e.g., PolitiFact, DFRAC, India Today, Quint, BoomLive), and an interactive web dashboard.

---

## 🚀 Key Features

- **Multilingual Support**: Trained & evaluated on multilingual benchmarks including Bengali, Hindi, Tamil, Telugu, and English.
- **Evidence Retrieval**: Hybrid retrieval mechanism combining TF-IDF lexical matching and dense neural similarity over a dynamic evidence pool.
- **Continuous Fact-Checking Crawler**: Scrapes verified claim-verdict pairs and continuously updates both the dataset and the evidence pool (`evidence_pool.json`).
- **Live Search & Fact-Checking**: On-demand web evidence lookup and sentence selection.
- **Modern Web Dashboard**: Real-time claim verification interface, live crawler progress, and retrieval inspection.
- **RESTful API**: FastAPI-powered backend with endpoints for claim verification, crawler management, presets, and model metrics.

---

## 🛠️ Project Structure

```
IndicClaim/
├── backend/                  # FastAPI backend server & modules
│   ├── app.py                # Main FastAPI application
│   ├── config.py             # System paths and configuration
│   ├── data_pipeline.py      # Dataset loading and preprocessing
│   ├── retriever.py          # Evidence retrieval engine (BM25 / TF-IDF / Neural)
│   ├── sentence_selector.py  # Evidence sentence selection & re-ranking
│   ├── veracity_model.py     # XLM-RoBERTa veracity classification model
│   └── scraper/              # Fact-check scrapers & live search
│       ├── crawler.py        # Background crawler & evidence pool updater
│       └── live_search.py    # Live web fact-checking lookup
├── dataset/                  # Dataset files & evidence pool
│   ├── crawled_dataset.json  # Scraped fact-checked records
│   ├── evidence_pool.json    # Consolidated pool of evidence passages
│   ├── train_subtask1.json   # Training claims
│   └── dev_subtask1.json     # Validation / Development claims
├── frontend/                 # Web interface (HTML, CSS, JS)
├── saved_model/              # Fine-tuned XLM-RoBERTa model weights & config
├── retriever_cache/          # Cached retrieval indexes
├── requirements.txt          # Python dependencies
├── run_pipeline.py           # Pipeline verification test suite
└── test_scraped_data.py      # Benchmark evaluation script
```

---

## 📦 Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd IndicClaim
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚦 Running the System

### 1. Start the Web Server & Dashboard
Run using the provided batch file (Windows):
```cmd
run_server.bat
```
Or directly with Python / Uvicorn:
```bash
python backend/app.py
```
Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

### 2. Run Pipeline Diagnostics
```bash
python run_pipeline.py
```

### 3. Evaluate on Scraped Fact-Check Data
```bash
python test_scraped_data.py --limit 20
```

---

## 📡 API Endpoints

- `POST /api/verify` — Verify a claim text with automatic evidence retrieval and veracity classification.
- `GET /api/presets` — Sample claims in multiple languages for quick demonstration.
- `POST /api/crawl/start` — Trigger background crawling of new fact-check articles.
- `GET /api/crawl/status` — Get live crawler status and scraped record counts.
- `GET /api/metrics` — View dataset statistics and model performance metrics.
