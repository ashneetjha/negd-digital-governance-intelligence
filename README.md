# NeGD Digital Governance Intelligence Portal

AI-powered Governance Intelligence System for the **National e-Governance Division (NeGD)**, MeitY, Government of India.

Upload state governance reports (DOCX/PDF), generate semantic embeddings, and perform RAG-based analysis with citation-backed insights.

---

## Architecture

```
Frontend (Next.js 16 + Tailwind)
  → FastAPI Backend
    → Supabase (Postgres + pgvector)
    → SentenceTransformers (all-MiniLM-L6-v2)
    → Groq LLaMA 3.1 8B Instant (LLM)
```

## Features

- **Document Ingestion** — Upload DOCX/PDF reports with state & month metadata
- **Semantic Chunking** — Smart section extraction, overlap-based chunking
- **Vector Embeddings** — 384-dim SentenceTransformer embeddings in pgvector
- **RAG Analysis** — Multi-stage retrieval, reranking, context management
- **Month-to-Month Comparison** — Structured JSON diff with citations
- **Confidence Scoring** — Faithfulness validation, hallucination risk
- **System Diagnostics** — `/api/system/status` for Supabase, embeddings, Groq, strict-mode checks
- **Bilingual UI** — English + Hindi (next-intl), dark/light themes
- **Mobile Responsive** — Collapsible sidebar, adaptive layouts

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind CSS 3, Framer Motion |
| Backend | FastAPI, Pydantic Settings, structlog |
| Database | Supabase (Postgres + pgvector) |
| Embeddings | SentenceTransformers (all-MiniLM-L6-v2) |
| LLM | Groq (LLaMA 3.1 8B Instant) |
| Infra | Render (backend), Vercel/Netlify (frontend) |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- Supabase project with pgvector enabled

### 1. Clone & Setup Environment

```bash
git clone https://github.com/ashneetjha/negd-digital-governance-intelligence.git
cd negd-digital-governance-intelligence
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r requirements.txt
```

Create `.env` in the project root (see `infra/.env.example`):

```env
APP_ENV=development
DEBUG=true
ALLOWED_ORIGINS=["http://localhost:3000"]
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.1-8b-instant
STRICT_REAL_AI=true
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
RAG_TOP_K=8
CHUNK_SIZE=600
CHUNK_OVERLAP=100
MAX_UPLOAD_SIZE_MB=50
UPLOAD_DIR=/tmp/negd_uploads
```

Start backend:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs at: http://localhost:8000/api/docs

Run deployment preflight:

```bash
cd backend
..\.venv\Scripts\python.exe scripts\preflight.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Start frontend:

```bash
npm run dev
```

Open http://localhost:3000

---

## Deployment

### Backend — Render

1. Push code to GitHub
2. Connect repo on [Render](https://render.com)
3. Use `infra/render.yaml` as the blueprint
4. Set environment variables in Render dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GROQ_API_KEY`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend — Vercel

1. Import repo on [Vercel](https://vercel.com)
2. Set root directory to `frontend`
3. Set environment variable:
   - `NEXT_PUBLIC_API_URL` = `https://your-backend.onrender.com`
4. Deploy

Recommended production envs:
- `NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com`

### Frontend — Netlify (Alternative)

1. Import repo on [Netlify](https://netlify.com)
2. Build settings are in `infra/netlify.toml`
3. Set `NEXT_PUBLIC_API_URL` in environment variables
4. Install the `@netlify/plugin-nextjs` plugin

### Supabase Setup

Ensure the following are configured:
- `pgvector` extension enabled
- `reports` and `report_chunks` tables created
- `match_chunks` RPC function deployed
- `match_chunks_for_comparison` RPC function deployed
- Row Level Security configured

---

## Project Structure

```
negd-digital-governance-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py             # Pydantic settings
│   │   ├── routes/               # API endpoints
│   │   │   ├── ingest.py         # Document upload
│   │   │   ├── analysis.py       # RAG analysis
│   │   │   ├── compare.py        # Month comparison
│   │   │   └── reports.py        # Report management
│   │   ├── services/             # Business logic
│   │   │   ├── rag_service.py    # RAG pipeline
│   │   │   ├── embedding_service.py
│   │   │   ├── chunking_service.py
│   │   │   ├── parsing_service.py
│   │   │   └── comparison_service.py
│   │   ├── db/                   # Supabase client
│   │   └── utils/                # Logger, helpers
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   └── [locale]/(app)/       # i18n-routed pages
│   │       ├── dashboard/
│   │       ├── upload/
│   │       ├── analysis/
│   │       ├── compare/
│   │       ├── reports/
│   │       └── settings/
│   ├── components/layout/        # Header, Sidebar
│   ├── lib/utils.ts              # API client, constants
│   ├── messages/                 # en.json, hi.json
│   └── package.json
├── infra/
│   ├── render.yaml               # Render deployment config
│   ├── netlify.toml              # Netlify deployment config
│   ├── Dockerfile.backend        # Docker build
│   └── .env.example              # Environment template
├── ml/
│   ├── rag_pipeline.py
│   ├── embedding_pipeline.py
│   └── compare_pipeline.py
└── .gitignore
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `GROQ_API_KEY` | ✅ | Groq API key for LLM |
| `GROQ_MODEL` | ❌ | Default: `llama-3.1-8b-instant` |
| `STRICT_REAL_AI` | ❌ | Default: `true`; disables fallback AI paths |
| `EMBEDDING_MODEL` | ❌ | Default: `all-MiniLM-L6-v2` |
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL (frontend) |
| `ALLOWED_ORIGINS` | ❌ | CORS origins JSON array |

---

## Release Checklist

Before pushing production deploys:

1. Supabase migrations applied (`backend/app/db/migrations.sql`).
2. `python backend/scripts/preflight.py` passes.
3. `/health` and `/api/system/status` return healthy signals.
4. Upload → index → dashboard flow verified.
5. Analysis and Compare routes return citation-backed responses.
6. Mobile checks completed for 320x568, 390x844, 768x1024, 1366x768.

---

## License

MIT License · Developed by IIT Ropar for NeGD, MeitY
