# IndicClaimVer - AI-Powered Indic Evidence Claim Verification System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg)](https://pytorch.org/)
[![HuggingFace](https://img.shields.io/badge/MuRIL-google%2Fmuril--base--cased-yellow.svg)](https://huggingface.co/google/muril-base-cased)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4%2B-38B2AC.svg)](https://tailwindcss.com/)

**IndicClaimVer** is an AI-powered factual claim verification system designed for English and Indic languages (Hindi, Tamil, Bengali, Telugu, Malayalam, Gujarati, Kannada, etc.). Given a factual claim, the system retrieves relevant evidence from an indexed multi-thousand evidence corpus using multilingual sentence transformers, ranks the top candidates, and evaluates factuality with a fine-tuned **MuRIL** (`google/muril-base-cased`) sequence classification model to produce an aggregated verdict (`SUPPORTS` or `REFUTES`) along with granular evidence-level confidence scores.

---

## 🚀 Key Features

- **End-to-End Neural Pipeline**:
  $$\text{User Claim} \longrightarrow \text{Indic Preprocessing} \longrightarrow \text{Vector Retrieval (Top-20)} \longrightarrow \text{Ranking (Top-5)} \longrightarrow \text{MuRIL Inference} \longrightarrow \text{Relevance-Weighted Aggregation} \longrightarrow \text{Interactive Verdict}$$
- **Indic Script & Unicode Preservation**: Normalizes whitespace while preserving Indian script characters, matras, accents, and punctuation.
- **Fast Multilingual Vector Retrieval**: Embeds claims using `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` with persistent disk embedding cache (`.npz`) for fast startup and inference.
- **Fine-Tuned MuRIL Sequence Classification**: Feeds `[CLS] Claim [SEP] Evidence [SEP]` pairs into the fine-tuned model once loaded into GPU/CPU memory.
- **Weighted Multi-Evidence Aggregation**: Aggregates per-evidence probabilities weighted by cosine retrieval similarity for transparent decision-making.
- **Graceful Fallback**: Detects `INSUFFICIENT_EVIDENCE` states when no evidence passages match above the similarity threshold.
- **Modern AI Research UI**: Sleek dark interface with glassmorphic cards, live pipeline visualizer, expandable evidence cards with copy snippets, and local verification history.

---

## 📁 Project Architecture

```
IndicClaimVer/
├── backend/
│   ├── app/
│   │   ├── config.py                 # Centralized configuration & device detection
│   │   ├── main.py                   # FastAPI app with lifespan model loading & CORS
│   │   ├── models/
│   │   │   └── schemas.py            # Pydantic request/response schemas
│   │   ├── routes/
│   │   │   └── verification.py       # API endpoints (/api/verify, /api/health)
│   │   ├── services/
│   │   │   ├── claim_verifier.py     # Fine-tuned MuRIL inference service
│   │   │   ├── evidence_ranker.py    # Modular ranking & candidate filtering
│   │   │   ├── evidence_retriever.py # Multilingual sentence embedding index
│   │   │   └── pipeline.py           # End-to-end pipeline coordination
│   │   └── utils/
│   │       └── preprocessing.py      # Indic-safe text normalization
│   ├── data/
│   │   ├── evidence_pool.json        # 50,000+ factual evidence database
│   │   └── evidence_embeddings.npz   # Cached precomputed embeddings
│   ├── models/
│   │   ├── muril_claim_verification_model/ # Fine-tuned MuRIL weights & tokenizer
│   │   │   ├── config.json
│   │   │   ├── model.safetensors
│   │   │   ├── tokenizer.json
│   │   │   └── tokenizer_config.json
│   │   └── label_mapping.json        # Label mapping (REFUTES: 0, SUPPORTS: 1)
│   ├── requirements.txt              # Backend dependencies
│   └── run.py                        # Server runner script
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInput.jsx         # Multiline prompt input with keybindings
│   │   │   ├── ChatWindow.jsx        # Welcome screen, example cards, & message feed
│   │   │   ├── ConfidenceBar.jsx     # Sleek confidence progress metric
│   │   │   ├── EvidenceCard.jsx      # Expandable card with per-evidence prediction
│   │   │   ├── LoadingAnalysis.jsx   # Real-time pipeline step progression animation
│   │   │   ├── MessageBubble.jsx     # User query & AI verification response bubble
│   │   │   ├── PipelineStatus.jsx    # 5-stage status visualizer
│   │   │   ├── Sidebar.jsx           # Nav, history, system status & pipeline info
│   │   │   └── VerdictCard.jsx       # Prominent SUPPORTS/REFUTES banner
│   │   ├── pages/
│   │   │   └── Home.jsx              # Main application page
│   │   ├── services/
│   │   │   └── api.js                # Frontend API client
│   │   ├── App.jsx
│   │   ├── index.css                 # Dark research theme & glassmorphism
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites
- **Python**: 3.10+ (tested on Python 3.13)
- **Node.js**: v18+ (tested on Node v24)
- **CUDA GPU** (Optional): Automatically utilized if available, defaults smoothly to CPU.

---

### 1. Backend Setup

1. Open a terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Install the required Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Verify Model and Evidence Dataset placement:
   - Ensure the trained model files are located in `backend/models/muril_claim_verification_model/`
   - Ensure `backend/models/label_mapping.json` exists:
     ```json
     {
       "REFUTES": 0,
       "SUPPORTS": 1
     }
     ```
   - Ensure `backend/data/evidence_pool.json` is present.

4. Run the FastAPI Backend Server:
   ```bash
   python run.py
   # Or using uvicorn directly:
   uvicorn app.main:app --reload --port 8000
   ```
   *The server will start at `http://localhost:8000`. On first launch, it precomputes and caches sentence embeddings.*

---

### 2. Frontend Setup

1. Open a second terminal and navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Launch the Vite Development Server:
   ```bash
   npm run dev
   ```
   *The frontend will start at `http://localhost:5173` and automatically proxy API calls to `http://localhost:8000`.*

---

## 🌐 API Specification

### `POST /api/verify`
Verify a factual claim.

**Request Body:**
```json
{
  "claim": "Tamil Nadu government extended Covid-19 curbs till January 31."
}
```

**Response Body:**
```json
{
  "claim": "Tamil Nadu government extended Covid-19 curbs till January 31.",
  "verdict": "SUPPORTS",
  "confidence": 0.9412,
  "supports_score": 0.9412,
  "refutes_score": 0.0588,
  "summary": "Based on the retrieved evidence, the claim is supported with 94% confidence. The system evaluated 5 relevant evidence passages...",
  "evidence": [
    {
      "rank": 1,
      "id": "EV/100002",
      "text": "Tamil Nadu Health Minister MA Subramanian on Tuesday, January 11 commented on the Covid-19 and the lockdown situation in the state...",
      "retrieval_score": 0.8845,
      "prediction": "SUPPORTS",
      "confidence": 0.9634
    }
  ],
  "processing": {
    "claim_analysis": "completed",
    "evidence_retrieval": "completed",
    "evidence_ranking": "completed",
    "verification": "completed"
  },
  "model_name": "MuRIL (google/muril-base-cased fine-tuned)"
}
```

### `GET /api/health`
Check pipeline initialization and system status.

**Response:**
```json
{
  "status": "healthy",
  "model": "loaded",
  "evidence_pool": "loaded",
  "evidence_count": 54454,
  "device": "cpu",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
}
```

---

## 🧪 Testing with Example Claims

| Language | Sample Claim | Expected Outcome |
| :--- | :--- | :--- |
| **English** | `Tamil Nadu extended existing Covid-19 curbs till January 31.` | `SUPPORTS` |
| **English** | `Odisha reported 14 new cases of the Omicron variant.` | `SUPPORTS` |
| **Hindi** | `सुप्रीम कोर्ट ने सर्दियों में शहरी गरीबों के लिए पर्याप्त आश्रय गृहों की मांग पर हलफनामा मांगा।` | `SUPPORTS` |
| **Bengali** | `করোনা মহামারি মোকাবিলায় প্রধানমন্ত্রীর ত্রাণ তহবিলে অর্থ দান করেছেন হীরাবেন।` | `SUPPORTS` |
| **English** | `India GDP contracted by 99% in 2024 according to official records.` | `REFUTES` / Low support |

---

## 🛡️ License
Built for academic and research factual claim verification.
