NeGD Digital Governance Intelligence Portal
===========================================

AI-powered Governance Intelligence System for the **National e-Governance Division (NeGD)**, MeitY, Government of India.

Developed by **IIT Ropar** in collaboration with NeGD, this system automates the ingestion of monthly state-level reports to provide prompt-driven extraction, comparative analysis, and high-level governance insights.

🏛️ Project Vision
------------------

The portal eliminates the manual overhead of analyzing text-heavy monthly reports. It provides a prompt-driven intelligence layer using **Retrieval-Augmented Generation (RAG)**, enabling officials to derive qualitative insights and case studies grounded strictly in the provided report content.

🏗️ Architecture
----------------

Plaintext

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   Frontend (Next.js 14 + Tailwind) [cite: 347, 349]    → FastAPI Backend (Secure Inference Layer) [cite: 367, 371]      → Supabase (Postgres + pgvector)       → SentenceTransformers (all-MiniLM-L6-v2)       → Groq LLaMA 3.1 8B Instant (LLM)   `

✨ Premium Features
------------------

*   **Semantic Document Ingestion**: Intelligent extraction and chunking of DOCX/PDF reports.
    
*   **Vector-Based Intelligence**: 384-dim semantic embeddings stored in pgvector for high-speed contextual retrieval.
    
*   **Comparative Intelligence**: Structured JSON comparisons detecting month-to-month initiatives, improvements, and compliance gaps.
    
*   **Hallucination Control**: Strict RAG grounding with deterministic generation and automated citation enforcement.
    
*   **GovTech UI**: Premium glassmorphic interface with bilingual support (English/Hindi) and mobile-first responsive design.
    
*   **Diagnostics Dashboard**: Real-time system health checks for database connectivity and AI model readiness.
    

🛠️ Tech Stack
--------------

**LayerTechnologyFrontend**

Next.js 14 (App Router) , TypeScript , Tailwind CSS , Framer Motion , next-intl

**Backend**

FastAPI , Pydantic , Structlog , Docker

**Database**

Supabase (PostgreSQL) + pgvector extension

**Embeddings**

local SentenceTransformers (all-MiniLM-L6-v2)

**LLM**Groq (LLaMA 3.1 8B Instant)**Infra**

Render (Backend) , Netlify/Vercel (Frontend)

🚀 Quick Start (Local Development)
----------------------------------

### 1\. Backend Setup

Bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd backend  python -m venv .venv  # Activate: .venv\Scripts\activate (Win) or source .venv/bin/activate (Unix)  pip install -r requirements.txt   `

**Environment Variables (.env):**Set your SUPABASE\_URL, SUPABASE\_KEY, and GROQ\_API\_KEY. Set STRICT\_REAL\_AI=true to enforce grounded RAG responses.

**Run Preflight & Start:**

Bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python scripts/preflight.py  # Verify environment health [cite: 35, 149]  uvicorn app.main:app --reload [cite: 168]   `

### 2\. Frontend Setup

Bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   cd frontend  npm install [cite: 161]  npm run dev [cite: 164]   `

🌐 Production Deployment
------------------------

### Backend — Render

### Frontend — Netlify

📁 Project Structure
--------------------

*   backend/: FastAPI application, ingestion pipelines, and database migrations.
    
*   frontend/: Next.js portal with internationalization (i18n) and GovTech components.
    
*   ml/: Centralized prompt governance (system\_prompt.txt) and RAG pipelines.
    
*   infra/: Production deployment configurations for Docker, Render, and Netlify.
    

⚖️ Governance & Compliance
--------------------------

*   **Zero Hallucination Policy**: All AI responses must be traceable to a source chunk.
    
*   **Audit Ready**: Every extraction includes state, month, and section citations.
    
*   **Open Source**: Built entirely on an open-source stack (Postgres, Python, Next.js).
    

Developed by Ashneet Jha ([ashneetjha.netlify.app](https://ashneetjha.netlify.app)), Intern at IIT Ropar for National e-Governance Division (NeGD), MeitY.