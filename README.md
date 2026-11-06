# Smart Farming AI

**AI-powered Smart Farming Assistant for small-scale Indian farmers**

Built with IBM Granite (`ibm/granite-4-h-small`) via IBM watsonx.ai, a Retrieval-Augmented Generation (RAG) pipeline using FAISS, a FastAPI backend, and a React + TypeScript frontend.

> **Hackathon project** — IBM Granite and IBM Cloud Lite integration are mandatory requirements. The application exclusively uses IBM Granite for all AI inference and never substitutes another LLM.

---

## Problem Statement

Small-scale farmers in India, particularly in Tamil Nadu and other rural regions, face critical information gaps:

- **No access to localised crop advice** — generic recommendations ignore soil composition, local climate, and seasonal conditions.
- **Language barrier** — most agricultural information is in English; Tamil-speaking farmers lack native-language advisory tools.
- **Fragmented data** — weather, market prices, soil reports, and pest identification require visiting multiple offices or services.
- **Delayed pest response** — by the time a disease is identified, significant crop loss has already occurred.

**Smart Farming AI** bridges these gaps by providing a single conversational interface — available in both English and Tamil — powered by IBM Granite and backed by verified agricultural knowledge documents.

---

## Project Objectives

1. Deliver AI-powered farming advice in **English and Tamil** using IBM Granite.
2. Provide **crop recommendations** based on NPK levels, pH, rainfall, and temperature.
3. Provide **soil and fertilizer advisory** based on soil composition and crop type.
4. Identify **pest and disease risks** from crop symptoms and recommend remedies.
5. Display **real-time weather data** for any Indian city via OpenWeatherMap.
6. Surface **live mandi (market) commodity prices** from data.gov.in / Agmarknet.
7. Enable **upload of agricultural documents** (PDF/TXT) to grow the knowledge base at runtime.
8. Maintain a **RAG pipeline** so Granite answers are grounded in verified agronomic documents.
9. Ensure **data integrity** — never fabricate weather, price, or advisory data; label every response clearly.

---

## Features and Modules

| Module | Description | API Endpoint |
|---|---|---|
| **IBM Granite Chatbot** | Bilingual (EN/Tamil) conversational AI using RAG | `POST /api/chat` |
| **Crop Recommendation** | Suggests best crops from soil & climate inputs | `POST /api/crop-recommend` |
| **Weather Advisory** | Live weather data with farming implications | `GET /api/weather/{location}` |
| **Soil & Fertilizer Advisory** | Fertilizer prescription from NPK + pH + soil type | `POST /api/soil-advisory` |
| **Pest & Disease Advisory** | Identifies pests/diseases from symptoms | `POST /api/pest-advisory` |
| **Mandi Price Tracker** | Live commodity prices from data.gov.in | `GET /api/mandi-prices` |
| **RAG Knowledge Base** | Upload PDF/TXT docs, FAISS-indexed for retrieval | `POST /api/kb/upload` |
| **Granite Connection Test** | Verifies IBM Cloud credentials + Tamil probe | `GET /api/granite/test` |
| **Health Check** | Liveness probe | `GET /api/health` |

---

## Technology Stack

| Layer | Technology | Version |
|---|---|---|
| **Frontend** | React | 19.x |
| | TypeScript | 7.x |
| | Vite | 8.x |
| | Tailwind CSS | 4.x |
| | React Router | 7.x |
| | Recharts | 3.x |
| | Axios | 1.x |
| **Backend** | Python | 3.10+ |
| | FastAPI | 0.115.5 |
| | Uvicorn | 0.32.0 |
| | Pydantic Settings | 2.6.1 |
| **AI / LLM** | IBM Granite (`ibm/granite-4-h-small`) | via `ibm-watsonx-ai` SDK 1.1.16 |
| **RAG / Embeddings** | Sentence Transformers (LaBSE) | 3.3.1 |
| | FAISS (CPU) | 1.9.0 |
| **Document Processing** | pdfplumber, PyPDF2 | — |
| **Language Detection** | langdetect | 1.0.9 |
| **Weather API** | OpenWeatherMap | Free tier |
| **Market Price API** | data.gov.in / Agmarknet | Free tier |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                  │
│  Landing · Dashboard · ChatBot · CropRecommendation      │
│  WeatherDashboard · SoilAdvisory · PestDisease           │
│  MandiPrices · KnowledgeBase · GraniteStatus             │
└────────────────────┬────────────────────────────────────┘
                     │  HTTP / REST (Axios)
                     ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (Uvicorn)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │  /chat   │ │ /weather │ │  /crop   │ │   /soil   │  │
│  │  /pest   │ │  /mandi  │ │  /kb     │ │ /granite  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └─────┬─────┘  │
│       │             │             │              │        │
│  ┌────▼─────────────▼─────────────▼──────────────▼────┐ │
│  │              Service Layer                          │ │
│  │  GraniteService · RAGService · WeatherService       │ │
│  │  CropService · SoilService · PestService            │ │
│  │  MandiService · DocumentLoader · VectorStore        │ │
│  └────┬────────────────────────────────────────────────┘ │
└───────┼─────────────────────────────────────────────────┘
        │
   ┌────┴───────────────────────────────────────┐
   │                                            │
   ▼                                            ▼
┌─────────────────────┐          ┌──────────────────────────┐
│  IBM watsonx.ai      │          │  External APIs            │
│  ibm/granite-4-h-   │          │  · OpenWeatherMap         │
│  small               │          │  · data.gov.in (Mandi)   │
└─────────────────────┘          └──────────────────────────┘
        │
   ┌────▼─────────────────────────────┐
   │  RAG Pipeline                    │
   │  · FAISS vector index            │
   │  · LaBSE embeddings (768-dim)    │
   │  · PDF/TXT document loader       │
   │  · Chunk splitter (500 / 50)     │
   └──────────────────────────────────┘
```

---

## IBM watsonx.ai and IBM Granite Integration

### Model

The application uses **`ibm/granite-4-h-small`** — the active IBM Granite instruct model available for direct inference on IBM Cloud Lite (us-south, 2026).

| Model | Status |
|---|---|
| `ibm/granite-4-h-small` | ✅ Active — default |
| `ibm/granite-3-3-8b-instruct` | ❌ Withdrawn Feb 2026 |
| `ibm/granite-3-8b-instruct` | ❌ Withdrawn Feb 2026 |
| `ibm/granite-4-h-small-curated` | ❌ Deploy-on-demand only |

### IBM Cloud Lite Limits

- **300,000 tokens/month** — free
- **2 requests/second** rate limit
- Token usage is logged on every inference call

### Integration Details

- SDK: `ibm-watsonx-ai==1.1.16`
- Credentials loaded exclusively from environment variables (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL`)
- The application **never substitutes another LLM**. If Granite is unavailable it returns the exact IBM error.
- Every AI-generated response carries the disclaimer: *"This is AI-generated advisory. Verify with a local agricultural officer before making farming decisions."*

### Verify Connection

```
GET http://localhost:8000/api/granite/test
```

This endpoint:
- Sends a real English inference request
- Reports exact token usage and latency
- Runs a Tamil generation quality probe (experimental)
- Returns the exact IBM error if inference fails

---

## RAG and FAISS Implementation

### Architecture

```
User Question
     │
     ▼
LaBSE Encoder ──► 768-dim embedding
     │
     ▼
FAISS top-K search (default k=3)
     │
     ▼
Retrieved document chunks
     │
     ▼
Context-augmented prompt ──► IBM Granite ──► Answer + Sources
```

### Components

| Component | File | Description |
|---|---|---|
| `DocumentLoader` | `app/services/rag/document_loader.py` | Loads PDF (pdfplumber + PyPDF2 fallback) and TXT files |
| `TextChunker` | `app/services/rag/text_chunker.py` | Splits text into 500-token chunks with 50-token overlap |
| `VectorStore` | `app/services/rag/vector_store.py` | FAISS index management: build, persist, load, search |
| `RAGService` | `app/services/rag/rag_service.py` | Orchestrates retrieval → prompt construction → Granite inference |

### Embedding Model — LaBSE

- **Model**: `sentence-transformers/LaBSE` (Language-Agnostic BERT Sentence Embeddings)
- **Dimension**: 768
- **Languages**: 109, including English and Tamil
- **Cross-lingual**: Tamil queries can retrieve English documents and vice versa
- **Index**: FAISS `IndexFlatIP` (inner product on L2-normalised vectors)

### Seed Knowledge Base

The following documents are pre-loaded:
- `01_Rice.pdf` — ICAR rice cultivation guide
- `HORTICULTURE_111087b3.pdf` — TNAU horticulture guide
- `rice_guide.txt` — rice farming practices

Additional documents can be uploaded at runtime via the Knowledge Base page.

---

## External API Integrations

### OpenWeatherMap

- **Endpoint**: `GET /api/weather/{location}`
- **Free tier**: 60 calls/minute, current weather
- **Caching**: 600-second TTL to minimize API calls
- **Fallback**: Returns `data_status: UNAVAILABLE` if API key not configured — no fabricated data

### data.gov.in / Agmarknet Mandi Prices

- **Endpoint**: `GET /api/mandi-prices?commodity=&state=&district=`
- **Dataset**: `9ef84268-d588-465a-a308-a864a43d0070` (Agmarknet daily arrivals)
- **Free tier**: Government open data
- **Caching**: 3600-second TTL
- **Fallback**: Returns `data_status: UNAVAILABLE` if API key not configured

---

## Installation Instructions

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer
- An IBM Cloud account with watsonx.ai Runtime provisioned ([create free Lite account](https://cloud.ibm.com/registration))

### Clone the Repository

```bash
git clone https://github.com/srisakthivelumani/Smart-Farming-AI.git
cd Smart-Farming-AI
```

---

## Backend Startup Instructions

```bash
cd backend

# 1. Create a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env    # Windows
# cp .env.example .env    # macOS/Linux

# Open .env and fill in your credentials:
#   WATSONX_API_KEY     — IBM Cloud IAM API key
#   WATSONX_PROJECT_ID  — watsonx.ai project ID
#   OPENWEATHER_API_KEY — OpenWeatherMap key (optional)
#   DATAGOV_API_KEY     — data.gov.in key (optional)

# 4. Start the backend server
uvicorn main:app --reload --port 8000
```

Backend runs at: http://localhost:8000

---

## Frontend Startup Instructions

Open a **new terminal**:

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start the development server
npm run dev
```

Frontend runs at: http://localhost:5173

---

## API Documentation Instructions

With the backend running, visit:

| URL | Description |
|---|---|
| http://localhost:8000/docs | Swagger UI — interactive API explorer |
| http://localhost:8000/redoc | ReDoc — clean API reference |
| http://localhost:8000/api/health | Health check — JSON status |
| http://localhost:8000/api/granite/test | IBM Granite connection test |

---

## Environment Variables Reference

Copy `backend/.env.example` to `backend/.env` and fill in the values:

| Variable | Required | Description |
|---|---|---|
| `WATSONX_API_KEY` | ✅ Yes | IBM Cloud IAM API key — [create here](https://cloud.ibm.com/iam/apikeys) |
| `WATSONX_PROJECT_ID` | ✅ Yes | watsonx.ai project ID — Manage → General in your project |
| `WATSONX_URL` | ✅ Yes | Regional endpoint (default: `https://us-south.ml.cloud.ibm.com`) |
| `GRANITE_MODEL_ID` | ✅ Yes | Default: `ibm/granite-4-h-small` |
| `EMBEDDING_MODEL` | Optional | Default: `sentence-transformers/LaBSE` |
| `OPENWEATHER_API_KEY` | Optional | [Get free key](https://openweathermap.org/api) |
| `DATAGOV_API_KEY` | Optional | [Register at data.gov.in](https://data.gov.in) |

> **Security**: `.env` is in `.gitignore` and is **never** committed. Never paste credentials into source code or chat.

---

## Project Structure

```
Smart-Farming-AI/
├── .gitignore
├── README.md
│
├── backend/
│   ├── main.py                         # FastAPI app entry point
│   ├── requirements.txt                # Python dependencies
│   ├── .env.example                    # Credential template (safe to commit)
│   │
│   └── app/
│       ├── api/                        # Route handlers
│       │   ├── chat.py                 # POST /api/chat
│       │   ├── crop.py                 # POST /api/crop-recommend
│       │   ├── granite.py              # GET  /api/granite/test
│       │   ├── health.py               # GET  /api/health
│       │   ├── knowledge.py            # POST /api/kb/upload, GET /api/kb/documents
│       │   ├── mandi.py                # GET  /api/mandi-prices
│       │   ├── pest.py                 # POST /api/pest-advisory
│       │   ├── soil.py                 # POST /api/soil-advisory
│       │   └── weather.py              # GET  /api/weather/{location}
│       │
│       ├── services/
│       │   ├── granite_service.py      # IBM watsonx.ai / Granite integration
│       │   ├── crop_service.py
│       │   ├── soil_service.py
│       │   ├── pest_service.py
│       │   ├── mandi_service.py
│       │   ├── weather_service.py
│       │   └── rag/
│       │       ├── document_loader.py  # PDF + TXT loader
│       │       ├── text_chunker.py     # Chunk splitter
│       │       ├── vector_store.py     # FAISS index manager
│       │       └── rag_service.py      # RAG orchestrator
│       │
│       ├── models/                     # Pydantic request/response schemas
│       │   ├── chat.py
│       │   ├── crop.py
│       │   ├── pest.py
│       │   └── soil.py
│       │
│       ├── core/
│       │   ├── config.py               # All settings from env vars
│       │   ├── exceptions.py           # Typed errors + handlers
│       │   └── dependencies.py         # FastAPI DI providers
│       │
│       └── data/
│           └── knowledge_base/         # Seed agricultural documents
│               ├── 01_Rice.pdf
│               ├── HORTICULTURE_111087b3.pdf
│               └── rice_guide.txt
│
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── tsconfig.json
    ├── package.json
    │
    └── src/
        ├── App.tsx                     # Root component + routing
        ├── main.tsx                    # Entry point
        ├── index.css                   # Global styles (Tailwind)
        ├── services/
        │   └── api.ts                  # Typed API client (Axios)
        ├── components/
        │   └── layout/
        │       └── Navbar.tsx
        └── pages/
            ├── Landing.tsx
            ├── Dashboard.tsx
            ├── ChatBot.tsx
            ├── CropRecommendation.tsx
            ├── WeatherDashboard.tsx
            ├── SoilAdvisory.tsx
            ├── PestDisease.tsx
            ├── MandiPrices.tsx
            ├── KnowledgeBase.tsx
            └── GraniteStatus.tsx
```

---

## Data Integrity Policy

Every response is clearly labelled with a data source badge:

| Badge | Meaning |
|---|---|
| 🟢 **LIVE** | Real-time data from a verified external API |
| 🔵 **RAG** | Retrieved from uploaded agricultural documents |
| 🟣 **AI** | Generated by IBM Granite |
| 🔴 **UNAVAILABLE** | API failed — no fabricated data is shown |

The application **never fabricates** weather, soil, or market price data.

---

## Limitations and Future Enhancements

### Current Limitations

- **Tamil support is experimental** — IBM Granite 4 H Small does not officially advertise Tamil language support; output quality in Tamil varies.
- **IBM Cloud Lite token limit** — 300,000 tokens/month. Heavy usage may exhaust the monthly quota.
- **FAISS is CPU-only** — large knowledge bases (>10,000 documents) will be slow to build.
- **Offline mode** — no caching layer for Granite responses; a network outage returns an error.
- **Mandi data freshness** — data.gov.in API sometimes has a 1–2 day lag on price updates.
- **No user authentication** — single-user application; not production-ready for multi-tenant deployment.

### Future Enhancements

- **Persistent conversation history** — store chat sessions in SQLite or Redis.
- **Voice input** — integrate Web Speech API for Tamil voice queries.
- **Push notifications** — weather alerts and pest outbreak warnings for registered farmers.
- **Offline PWA** — service worker caching for use in low-connectivity rural areas.
- **Photo-based pest identification** — integrate a vision model for leaf disease diagnosis from images.
- **Multi-language expansion** — add Telugu, Kannada, and Hindi via LaBSE cross-lingual retrieval.
- **Satellite imagery integration** — crop health indices (NDVI) from open satellite data.
- **Farmer profile** — personalised recommendations based on saved farm location, crop history, and soil reports.
- **Production deployment** — containerise with Docker, deploy backend to IBM Code Engine, frontend to IBM Cloud Object Storage static hosting.

---

## Acknowledgements

- [IBM watsonx.ai](https://www.ibm.com/watsonx) and [IBM Granite](https://www.ibm.com/granite) — `ibm-watsonx-ai` SDK
- [ICAR](https://icar.org.in) / [TNAU](https://www.tnau.ac.in) — agricultural knowledge sources
- [LaBSE](https://huggingface.co/sentence-transformers/LaBSE) — Google Research, Language-Agnostic BERT Sentence Embeddings
- [FAISS](https://github.com/facebookresearch/faiss) — Facebook AI Research
- [OpenWeatherMap](https://openweathermap.org) — weather data
- [data.gov.in](https://data.gov.in) — Government of India open data portal (Agmarknet)
