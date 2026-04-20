# NeGD Digital Governance Intelligence Portal 🏛️🤖

### AI-Powered Governance Intelligence System
**Collaboration:** National e-Governance Division (NeGD), MeitY, Government of India & IIT Ropar  
**Intern:** Ashneet Jha |

---

## 🎯 Project Objective
[cite_start]This system is designed to automate the analysis of monthly state-level governance reports[cite: 5]. By leveraging Retrieval-Augmented Generation (RAG), the portal converts semi-structured reports into a searchable intelligence layer, enabling:
* [cite_start]**Automated Ingestion:** Processing monthly state reports (DOCX/PDF)[cite: 6].
* [cite_start]**Contextual Querying:** Prompt-driven extraction of specific policy or compliance insights[cite: 61, 71].
* [cite_start]**Comparative Intelligence:** Month-to-month structured comparison to track state-wise progress and adoption gaps[cite: 67, 114].

---

## 🏗️ System Architecture
[cite_start]The project follows a modern RAG (Retrieval-Augmented Generation) workflow to ensure all AI responses are grounded in official government documents[cite: 73, 101].



### Technical Stack
* **Frontend:** Next.js 16 + Tailwind CSS
* **Backend:** FastAPI (Python)
* [cite_start]**Database:** Supabase (PostgreSQL) with `pgvector` for semantic search [cite: 8, 28]
* [cite_start]**Embeddings:** `paraphrase-MiniLM-L3-v2` (Sentence-Transformers) 
* [cite_start]**LLM:** Groq LLaMA 3.1 8B / Google Gemini (Deterministic configuration) [cite: 11, 28]

---

## ✅ Current Development Status (~90% Complete)

### Phase 1: Infrastructure & Data Layer (Completed)
* [cite_start]Supabase schema design with `report_chunks` and `pgvector`[cite: 8].
* [cite_start]Background ingestion pipeline with structured logging[cite: 8].

### Phase 2: RAG Intelligence Layer (Completed)
* [cite_start]Vector similarity retrieval using RPC functions[cite: 8, 11].
* [cite_start]Citation-backed responses to ensure traceability to source documents[cite: 11, 101].

### Phase 3: Comparative Engine (Completed)
* [cite_start]Cross-month retrieval and initiative detection[cite: 14].
* [cite_start]Structured JSON output for quantitative change extraction[cite: 14].

### Phase 4: Production Hardening (In Progress)
* [cite_start][x] CORS configuration & Error handling[cite: 17].
* [cite_start][ ] Rate limiting & Authentication layer[cite: 19, 20].
* [cite_start][ ] Final Deployment to Render/Netlify[cite: 32, 35].

---

## 🚀 Key Capabilities
* [cite_start]**Flexible Extraction:** Instead of hardcoded fields, the system uses natural language prompts to find adoption levels for schemes like DigiLocker[cite: 72, 75].
* [cite_start]**Trend Identification:** Automatically detects improvements or regressions in state performance over time[cite: 104].
* [cite_start]**Case Study Generation:** Derives qualitative insights directly from report text to highlight best practices[cite: 78, 118].

---

## 🛠️ Local Setup
1. **Clone the Repo:** `git clone https://github.com/your-repo/negd-intelligence.git`
2. **Backend:** Install requirements via `pip install -r requirements.txt` and set up your `.env` with Supabase and Groq/Gemini keys.
3. **Frontend:** Run `npm install` and `npm run dev`.