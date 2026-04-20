# NeGD Digital Governance Intelligence System — System Documentation

**Version:** 3.0.0 (Hybrid Intelligence)  
**Organization:** National e-Governance Division (NeGD), Ministry of Electronics & Information Technology (MeitY), Government of India  
**Last Updated:** April 2026

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND (Next.js — Netlify)                                   │
│  - Dashboard, Bilingual UI, MonthYearPicker                     │
│  - Analysis, Compare, Cross-State, Chat pages                   │
└────────────────────────┬────────────────────────────────────────┘
                         │  HTTPS REST API
┌────────────────────────▼────────────────────────────────────────┐
│  BACKEND (FastAPI — Render Free Tier)                            │
│                                                                 │
│  INTELLIGENT ROUTING LAYER (v3.0)                               │
│  ├── "compare X and Y"  → comparison_service                   │
│  ├── "trends/insights"  → insight_service                      │
│  └── everything else    → RAG pipeline (hybrid)                │
│                                                                 │
│  RAG PIPELINE (v3.0 — Hybrid Multi-Stage)                      │
│  ├── Query Rewriting      (LLM-based, 5s timeout)              │
│  ├── Hybrid Retrieval     (Vector + BM25 score fusion)         │
│  ├── Cross-Encoder Rerank (HF API, top 10 → top 5)            │
│  ├── Dual-Mode LLM Call   (strict / limited-evidence)          │
│  ├── 5-Metric Confidence  (composite scoring)                  │
│  ├── 4-Rule Verification  (auditability layer)                 │
│  └── Structured Output    (answer + key_points + citations)    │
│                                                                 │
│  routes/                                                        │
│  ├── analysis.py       — Intelligent routing + RAG              │
│  ├── compare.py        — Structured-extraction comparison       │
│  ├── insights.py       — Global intelligence (no LLM)          │
│  ├── chat.py           — General governance chatbot             │
│  ├── ingest.py         — PDF/DOCX upload + chunking            │
│  ├── reports.py        — Report listing / metadata             │
│  └── system.py         — Health + RAG quality metrics           │
│                                                                 │
│  services/                                                      │
│  ├── rag_service.py    — Hybrid RAG (BM25 + vector + reranker) │
│  ├── comparison_service.py — Structured-extraction comparison   │
│  ├── insight_service.py — Global insights engine                │
│  ├── embedding_service.py  — HF API + local SentenceTransformer│
│  ├── chat_service.py   — Direct LLM chatbot (constrained)      │
│  ├── evaluation_service.py — 5-metric scoring + health accum.  │
│  ├── verification_service.py — 4-rule auditability layer       │
│  ├── chunking_service.py — Text chunking                       │
│  └── parsing_service.py  — PDF/DOCX parsing                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  DATA LAYER (Supabase — PostgreSQL + pgvector)                  │
│  ├── reports         — Report metadata                          │
│  ├── report_chunks   — Embedded text chunks (384-dim vectors)   │
│  ├── match_chunks()  — pgvector similarity search RPC           │
│  └── match_chunks_for_comparison() — Comparison RPC             │
└─────────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│  ML / INFERENCE LAYER                                           │
│  ├── Groq (LLaMA 3.3-70B) — LLM inference + query rewriting    │
│  ├── HF Inference API      — Embeddings (remote, zero RAM)     │
│  ├── HF Inference API      — Cross-encoder reranking (remote)  │
│  └── rank-bm25             — BM25 keyword retrieval (in-memory)│
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/analysis` | Intelligent routing → RAG / comparison / insights |
| `POST` | `/api/analysis?debug=true` | Same + full evaluation metrics |
| `POST` | `/api/compare` | Same-state month-to-month comparison |
| `POST` | `/api/compare/cross-state` | Cross-state governance comparison |
| `POST` | `/api/chat` | General governance chatbot |
| `POST` | `/api/ingest` | Upload governance report (PDF/DOCX) |
| `GET`  | `/api/insights/global` | System-wide intelligence |
| `GET`  | `/api/reports` | List indexed reports |
| `GET`  | `/api/system/status` | System health + success_rate |
| `GET`  | `/api/ping` | Lightweight keep-alive |

### Analysis Response Schema (v3.0)

```json
{
  "success": true,
  "data": {
    "answer": "...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "citations": [{"state": "", "reporting_month": "", "section_type": "", "similarity_score": 0.75}],
    "sources": [...],
    "confidence": 0.82,
    "mode": "strict",
    "status": "ok",
    "retrieval_method": "hybrid",
    "reranker_applied": true,
    "query_rewritten": true,
    "routed_to": "rag"
  }
}
```

---

## 3. Hybrid Retrieval Pipeline (v3.0)

### Stage 1: Query Rewriting
- LLM rewrites user query for better retrieval terms
- Strict 5-second timeout; falls back to original query on failure
- Example: "how is DigiLocker doing?" → "DigiLocker digital governance adoption progress compliance status"

### Stage 2: Hybrid Retrieval (Vector + BM25 Fusion)

```
┌──────────────────────┐    ┌──────────────────────┐
│  Vector Retrieval    │    │  BM25 Retrieval       │
│  (pgvector cosine)   │    │  (keyword matching)   │
│  semantic matching   │    │  exact term matching   │
└──────────┬───────────┘    └──────────┬────────────┘
           │                           │
           └─────────┬─────────────────┘
                     │
              Score Fusion
         final = 0.5*vector + 0.5*bm25
                     │
              ┌──────▼──────┐
              │  Top-K Fused │
              └──────────────┘
```

**BM25 Details:**
- Index built lazily per state/month, cached 10 minutes
- Max 500 chunks per index to prevent OOM
- Pure Python (`rank-bm25`) — no torch dependency
- Falls back to vector-only if BM25 unavailable

### Stage 3: Cross-Encoder Reranking
- Takes top 10 fused candidates
- Scores relevance using `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Runs via HuggingFace Inference API (zero local RAM)
- Selects top 5 for final context
- Falls back to diversity reranking on API failure

### Stage 4: Answer Generation
- Dual-mode system prompt (strict / limited-evidence)
- LLM call with 3x retry and 15s timeout
- Structured output: answer + key_points extracted

---

## 4. Intelligent Routing (v3.0)

The `/api/analysis` endpoint automatically routes queries based on intent:

| Pattern | Route | Example |
|---------|-------|---------|
| Contains "compare" + "and"/"vs" | Cross-state comparison | "Compare Delhi and Kerala" |
| Contains "trend"/"insight"/"overview" (no state) | Global insights | "What are emerging trends?" |
| Everything else | RAG pipeline | "DigiLocker adoption in Maharashtra" |

**Safety:** Every route falls back to RAG on failure.

---

## 5. Confidence Scoring

### Formula

```
confidence = keyword_match×0.25 + entity_consistency×0.25 +
             citation_density×0.20 + retrieval_hit×0.20 +
             (1 - latency_penalty)×0.10
```

### Rationale

| Metric | Weight | Why |
|--------|--------|-----|
| **Keyword Match** | 0.25 | Semantic alignment — response stays on-topic |
| **Entity Consistency** | 0.25 | Scope correctness — prevents state/scheme drift |
| **Citation Density** | 0.20 | Grounding strength — defensibility under audit |
| **Retrieval Hit** | 0.20 | Retrieval correctness — at least one strong match |
| **Latency Penalty** | 0.10 | System health indicator |

**Future Work:** Confidence calibration using labeled datasets and learned weighting models.

---

## 6. Failure Handling

| Status | Trigger | Response |
|--------|---------|----------|
| `no_data` | 0 chunks after filtering | No LLM call, instant response |
| `low_confidence` | confidence < 0.40 | Answer + disclaimer |
| `ok` | confidence ≥ 0.40 | Full grounded response |

---

## 7. Verification Rules (4)

| Rule | Check | Latency |
|------|-------|---------|
| Citation presence | Non-"not found" must have ≥1 source | <1ms |
| State-scope alignment | Answer must reference queried state | <1ms |
| Consistency | No "not found" when sources exist | <1ms |
| Unsupported claims | ≥2 ungrounded numeric claims | <1ms |

---

## 8. Performance Safety (v3.0)

| Safeguard | Mechanism |
|-----------|-----------|
| Query rewrite timeout | 5s strict timeout, fallback to original |
| BM25 index limit | Max 500 chunks per index |
| BM25 cache | 10-minute TTL, prevents rebuild per query |
| Reranker limit | Top 10 → top 5 only |
| Reranker timeout | 8s HF API timeout, fallback to diversity |
| LLM timeout | 15s with 3x retry |
| Overall fallback | Any stage failure → original pipeline continues |

---

## 9. Deployment

### Backend (Render Free Tier)

```bash
pip install -r requirements-render.txt
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**RAM budget:** ~250MB (no torch, no local models)
- Embeddings: HF Inference API (remote)
- Reranker: HF Inference API (remote)
- BM25: Pure Python (rank-bm25 + numpy)

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `GROQ_API_KEY` | ✅ | Groq API key |
| `HF_API_TOKEN` | ✅ (prod) | HF API — embeddings + reranker |
| `ALLOWED_ORIGINS` | ✅ | Frontend URL(s) |

---

## 10. Error Handling Design

The backend implements unified, global error handling via FastAPI exception handlers to ensure all services return a consistent JSON shape across both managed (`HTTPException`) and unmanaged (`Exception`) errors.

**Standard Error Payload:**
```json
{
  "error": true,
  "error_type": "ValueError",
  "message": "Internal Server Error",
  "details": "Specific stack trace or validation issue",
  "fallback_used": false
}
```

- **Unmanaged Exceptions:** Intercepted globally, logged with full stack traces securely to console without leaking system internals to users. Return HTTP 500.
- **Validation Errors (Pydantic):** Captured and transformed into HTTP 422 with precise validation details.
- **No Silent Failures:** Core processes (chunking, RAG generation, configuration loading) are explicitly written to raise exceptions immediately rather than proceeding with 0 items, ensuring ingestion and query processes fail loudly and securely.

---

*NeGD Digital Governance Intelligence System v3.0.0 — Hybrid Intelligence*
