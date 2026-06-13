# MedMentor AI — MBBS Medicine AI Tutor

> Intelligent AI tutor for MBBS students powered by your Medicine textbook, ChromaDB RAG, and Groq/Gemini LLMs.

---

## 🗂 Project Structure

```
MBBS Medicine AI Tutor/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # MongoDB (Motor)
│   │   ├── chroma_client.py     # ChromaDB client
│   │   ├── llm.py               # Groq + Gemini wrapper
│   │   ├── agents/
│   │   │   ├── explain_agent.py # RAG explain
│   │   │   ├── case_agent.py    # Clinical case gen
│   │   │   └── test_agent.py    # MCQ generation
│   │   └── routers/
│   │       ├── topics.py
│   │       ├── cases.py
│   │       ├── tests.py
│   │       └── progress.py
│   ├── ingest_pdf.py            # Phase 1: PDF → ChromaDB + MongoDB
│   ├── verify_retrieval.py      # Spot-check retrieval
│   ├── requirements.txt
│   └── .env                     # ← Fill in your API keys here!
└── frontend/
    └── src/
        ├── components/          # Sidebar, Chat, Case, Test, Dashboard
        ├── views/               # Home, Topic, Test
        ├── stores/              # Pinia: topics, chat, test
        └── api/index.js         # Axios API client
```

---

## ⚡ Quick Start

### Step 1 — Configure `.env`

Edit `backend/.env`:
```env
GROQ_API_KEY=your_actual_groq_api_key
GEMINI_API_KEY=your_actual_gemini_api_key
MEDICINE_PDF_PATH=C:\path\to\your\medicine.pdf
MONGO_URI= mongodb uri
MONGO_DB=db name
CHROMA_PERSIST_DIR=./chroma_db
```

Get API keys:
- **Groq**: https://console.groq.com (free tier available)
- **Gemini**: https://aistudio.google.com/apikey

### Step 2 — Install Python dependencies

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Step 3 — Ingest your PDF (one-time, ~10–30 min)

```powershell
# In backend/ with venv activated:
python ingest_pdf.py

# Verify retrieval quality:
python verify_retrieval.py --query "heart failure"
python verify_retrieval.py --query "myocardial infarction"
```

Use `--reset` flag to re-run ingestion from scratch:
```powershell
python ingest_pdf.py --reset
```

### Step 4 — Start the backend

```powershell
# Option A: batch script
start_backend.bat

# Option B: manual
cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Step 5 — Start the frontend

```powershell
# Option A: batch script
start_frontend.bat

# Option B: manual
cd frontend && npm run dev
```

App URL: http://localhost:5173

---

## 🧪 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chapters` | List all chapters |
| GET | `/api/topics?chapter_id=` | List topics |
| GET | `/api/topics/search?q=` | Search topics |
| POST | `/api/topic/{id}/explain` | RAG explain (streaming SSE) |
| POST | `/api/topic/{id}/case` | Generate clinical case |
| POST | `/api/test/generate` | Generate MCQs |
| POST | `/api/test/submit` | Submit answer + SR update |
| GET | `/api/test/daily` | Today's due questions |
| GET | `/api/progress` | Overall stats |
| GET | `/api/progress/due` | Topics due today |
| GET | `/api/progress/calendar` | Heatmap data |

---

## 🗄 MongoDB Collections (db: `jarvis`)

| Collection | Purpose |
|------------|---------|
| `med_chapters` | Chapter/system metadata |
| `med_topics` | Per-disease topic metadata |
| `med_chat_sessions` | Chat history per topic |
| `med_cases` | Generated clinical cases |
| `med_tests` | Generated MCQs |
| `med_test_attempts` | User answers + correctness |
| `med_progress` | Spaced repetition tracker |

---

## 🔁 Spaced Repetition Logic

- **Correct answer** → interval doubles: 1 → 3 → 7 → 14 → 30 → 60 days
- **Wrong answer** → resets to 1 day
- `GET /api/test/daily` returns all topics where `next_due_date ≤ today`

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + Vite + Pinia + Vue Router |
| Backend | Python FastAPI + Uvicorn |
| Vector DB | ChromaDB (local persistent) |
| Database | MongoDB (Motor async) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM Primary | Groq llama-3.3-70b-versatile |
| LLM Fallback | Google Gemini 1.5 Flash |
| PDF Parsing | PyMuPDF (fitz) |
