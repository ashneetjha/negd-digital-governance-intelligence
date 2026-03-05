"""
NeGD Digital Governance Intelligence Portal
FastAPI Backend — Application Entry Point
"""

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routes import ingest, analysis, compare, reports, system
from app.services.embedding_service import warmup_embedding_model
from app.utils.logger import get_logger

logger = get_logger(__name__)

APP_VERSION = "1.0.0"

app = FastAPI(
    title="NeGD Digital Governance Intelligence Portal API",
    description=(
        "Backend API for the National e-Governance Division (NeGD), MeitY. "
        "Provides document ingestion, RAG-based intelligence analysis, "
        "and comparative governance reporting."
    ),
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ──────────────────────────────────────────────────────────────
# CORS Configuration - Hardened for Production
# ──────────────────────────────────────────────────────────────

# Render (and other PaaS dashboards) may deliver ALLOWED_ORIGINS as:
#   • A proper JSON array string:  '["https://a.com","https://b.com"]'
#   • A bare single URL:           'https://a.com'
#   • A comma-separated list:      'https://a.com, https://b.com'
#   • An empty or whitespace-only string (mis-saved dashboard value)
# We normalise all these cases into a clean Python list.

def _parse_origins(raw) -> list[str]:
    if isinstance(raw, list):
        origins = raw
    elif isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            origins = []
        elif stripped.startswith("["):
            try:
                origins = json.loads(stripped)
            except json.JSONDecodeError:
                # Malformed JSON — treat whole thing as a single origin
                origins = [stripped]
        elif "," in stripped:
            # Comma-separated list (common in PaaS dashboard env vars)
            origins = [o.strip() for o in stripped.split(",")]
        else:
            origins = [stripped]
    else:
        origins = []

    # Remove blanks and duplicates while preserving order
    seen: set[str] = set()
    cleaned: list[str] = []
    for o in origins:
        o = o.strip().rstrip("/")
        if o and o not in seen:
            seen.add(o)
            cleaned.append(o)

    return cleaned or ["http://localhost:3000"]


allowed_origins = _parse_origins(settings.ALLOWED_ORIGINS)

# Always include the canonical production URL
_PRODUCTION_URL = "https://negd-digital-governance-intelligence.netlify.app"
if _PRODUCTION_URL not in allowed_origins:
    allowed_origins.append(_PRODUCTION_URL)

# ── Force production settings when running on Render ─────────────────────────
# Render injects RENDER=true automatically; use it as a reliable gate.
if os.environ.get("RENDER") == "true" and settings.APP_ENV != "production":
    logger.warning(
        "APP_ENV is not 'production' on Render — overriding to 'production'",
        detected_env=settings.APP_ENV,
    )
    os.environ["APP_ENV"] = "production"
    settings.APP_ENV = "production"   # type: ignore[misc]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────────────────────
# Startup / Shutdown Hooks
# ──────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info(
        "NeGD API starting",
        environment=settings.APP_ENV,
        debug=settings.DEBUG,
        version=APP_VERSION,
        allowed_origins=allowed_origins,
    )
    # Pre-warm the embedding model in the background so it is ready
    # before the first real request arrives (avoids cold-start timeouts).
    warmup_embedding_model()
    logger.info("Embedding model warmup triggered (background thread)")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("NeGD API shutting down")


# ──────────────────────────────────────────────────────────────
# Register Routers
# ──────────────────────────────────────────────────────────────

app.include_router(ingest.router, prefix="/api", tags=["Ingest"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(compare.router, prefix="/api", tags=["Comparison"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(system.router, prefix="/api", tags=["System"])


# ──────────────────────────────────────────────────────────────
# Health + Root
# ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.APP_ENV,
            "version": APP_VERSION,
            "service": "negd-digital-governance-intelligence-api",
        },
        status_code=200,
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "NeGD Digital Governance Intelligence Portal API",
        "organization": "National e-Governance Division (NeGD), MeitY",
        "environment": settings.APP_ENV,
        "docs": "/api/docs",
        "health": "/health",
    }