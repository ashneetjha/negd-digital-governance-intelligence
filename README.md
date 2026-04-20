# NeGD Digital Governance Intelligence System

> **AI-Powered Governance Analytics Platform for the National e-Governance Division (NeGD), MeitY, Government of India**

A production-grade **hybrid AI intelligence system** that transforms governance reports into actionable insights. Built for decision-makers at NeGD, MeitY, and state-level digital governance teams.

## ✨ Key Features

- **Hybrid RAG**: Uses a fusion of vector embeddings (pgvector) and exact match keyword search (BM25), optimized further with neural cross-encoder reranking.
- **Document Ingestion (PDF/DOCX)**: Intelligent text parsing, chunking, and metadata extraction of structured tables and paragraphs from State Monthly Progress Reports.
- **Structured AI Outputs**: Guaranteed canonical AI outputs containing grounded answers, top insights, gaps, recommendations, and confidence evaluations.
- **Governance Dashboards**: Analytics interface for rapid visualization of intelligence, risk alerts, and emerging governance trends.
- **State Ranking & Gap Analysis**: Multi-dimensional ranking of states on criteria like Activity Level, Innovation Signals, Initiative Diversity, and Timeliness.

## 🏛️ Architecture Overview

The platform uses a scalable microservice design divided into an intuitive React frontend and a heavy-lifting intelligent FastAPI backend:

- **Frontend (Next.js)**: Rich analytics dashboard with bilingual support, dark mode toggles, and hydration-safe SSR rendering.
- **Intelligent Routing**: Determines if a query should target document retrieval (RAG), cross-state comparison, or global insight extraction.
- **AI Processing Pipeline**:
  - LLM-powered Query Rewriting
  - Hybrid Retrieval (Vector + Keyword)
  - HF API Cross-Encoder Reranking
  - Confidence Scoring & 4-Rule Verification

## 🛠️ Tech Stack

- **Frontend**: Next.js 14, TailwindCSS, Framer Motion, TypeScript
- **Backend**: FastAPI, Pydantic, Uvicorn
- **Database**: Supabase PostgreSQL with `pgvector` extension
- **Machine Learning**: 
  - LLM: Groq LLaMA 3.3-70B Versatile
  - Embeddings & Reranking: HuggingFace Inference API (`intfloat/e5-small-v2`, `cross-encoder/ms-marco-MiniLM-L-6-v2`)

## 🚀 Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase Project with `pgvector`
- Groq API Key and HuggingFace API Token 

### Backend Setup

1. **Clone the repository and enter the backend directory**:
   ```bash
   git clone https://github.com/your-org/negd-digital-governance-intelligence.git
   cd negd-digital-governance-intelligence/backend
   ```
2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\Activate.ps1
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Frontend Setup

1. **Enter the frontend directory**:
   ```bash
   cd ../frontend
   ```
2. **Install dependencies**:
   ```bash
   npm install
   ```
3. **Start the frontend development server**:
   ```bash
   npm run dev
   ```

## ⚙️ Environment Variables

Create `.env` in the `backend/` directory:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbG...
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
HF_API_TOKEN=hf_...
ALLOWED_ORIGINS=http://localhost:3000
APP_ENV=development
```

Create `.env.local` in the `frontend/` directory (if different from default):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🌐 Deployment

### Backend (Render Free Tier)
Deploy using the Render Web Service specification.
- **Build Command**: `pip install -r requirements-render.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Ensure all Environment Variables are configured in the Render Dashboard. (No heavy local AI models are loaded; embeddings and rerankers use remote APIs). 

### Frontend (Netlify)
Connect your GitHub repository to Netlify.
- **Build Command**: `npm run build`
- **Publish Directory**: `.next`
- **Environment Variables**: Add `NEXT_PUBLIC_API_URL` pointing to your deployed backend.

## 🖼️ UI/Screenshots Description

The frontend features dynamic, responsive UI elements utilizing modern web design aesthetics:
- **System Status Dashboard**: Displays realtime connection capacities with the backend services through an interactive, glassmorphic diagnostic interface.
- **Governance Intelligence Dashboard**: A complex analytical grid exhibiting real-time rankings, top metrics, and interactive date-filters (MonthYear Picker). 
- **Compare States Interface**: Visually stunning dual-column comparison module mapping state metrics precisely.

---

### 👨‍💻 Author

**Ashneet Jha**  
Intern, IIT Ropar | SRM IST, KTR  
Portfolio: [https://ashneetjha.netlify.app/](https://ashneetjha.netlify.app/)