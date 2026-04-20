"""
NeGD Digital Governance Intelligence Portal
FastAPI Backend — Application Entry Point
"""

import json
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routes import ingest, analysis, compare, reports, system, chat, insights, intelligence
from app.services.embedding_service import warmup_embedding_model
from app.utils.logger import get_logger

logger = get_logger(__name__)

APP_VERSION = "3.0.0"
REQUIRED_GROQ_MODEL = "llama-3.3-70b-versatile"

app = FastAPI(
    title="NeGD Digital Governance Intelligence Portal API",
    description=(
        "Backend API for the National e-Governance Division (NeGD), MeitY. "
        "Provides document ingestion, RAG-based intelligence analysis, "
        "cross-state comparative governance reporting, and a general-purpose "
        "Digital India governance chatbot."
    ),
    version=APP_VERSION,
    docs_url="/docs",           
    redoc_url="/redoc",         
    openapi_url="/openapi.json" 
)

# ──────────────────────────────────────────────────────────────
# Exception Handlers
# ──────────────────────────────────────────────────────────────

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_type": "HTTPException",
            "message": str(exc.detail),
            "details": f"{request.method} {request.url.path}",
            "fallback_used": False
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_type": type(exc).__name__,
            "message": "Internal Server Error",
            "details": str(exc),
            "fallback_used": False
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "error_type": "ValidationError",
            "message": "Data Validation Failed",
            "details": str(exc.errors()),
            "fallback_used": False
        }
    )

# ──────────────────────────────────────────────────────────────
# CORS Configuration
# ──────────────────────────────────────────────────────────────

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
                origins = [stripped]
        elif "," in stripped:
            origins = [o.strip() for o in stripped.split(",")]
        else:
            origins = [stripped]
    else:
        origins = []

    seen: set[str] = set()
    cleaned: list[str] = []
    for o in origins:
        o = o.strip().rstrip("/")
        if o and o not in seen:
            seen.add(o)
            cleaned.append(o)

    return cleaned or ["http://localhost:3000"]

allowed_origins = _parse_origins(settings.ALLOWED_ORIGINS)

_PRODUCTION_URL = "https://negd-digital-governance-intelligence.netlify.app"
if _PRODUCTION_URL not in allowed_origins:
    allowed_origins.append(_PRODUCTION_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ──────────────────────────────────────────────────────────────
# Startup / Shutdown
# ──────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info(
        "NeGD API starting",
        environment=settings.APP_ENV,
        debug=settings.DEBUG,
        version=APP_VERSION,
        allowed_origins=allowed_origins,
        hf_api_enabled=bool(settings.HF_API_TOKEN),
    )

    # Warmup embeddings
    warmup_embedding_model()
    logger.info("Embedding model warmup triggered")

    # BM25 check
    try:
        import rank_bm25
        logger.info("BM25 module loaded successfully")
    except ImportError:
        logger.critical("rank_bm25 not installed")
        raise RuntimeError("BM25 not installed")

    # Env validation
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY missing")

    if not settings.HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN missing")

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Supabase config missing")

    logger.info("All critical environment variables validated")

    if settings.GROQ_MODEL != REQUIRED_GROQ_MODEL:
        logger.warning(
            "GROQ model mismatch",
            configured=settings.GROQ_MODEL,
            expected=REQUIRED_GROQ_MODEL,
        )
    else:
        logger.info("GROQ model validated")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("NeGD API shutting down")

# ──────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────

app.include_router(ingest.router, prefix="/api", tags=["Ingest"])
app.include_router(analysis.router, prefix="/api", tags=["Analysis"])
app.include_router(compare.router, prefix="/api", tags=["Comparison"])
app.include_router(reports.router, prefix="/api", tags=["Reports"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(insights.router, prefix="/api", tags=["Insights"])
app.include_router(intelligence.router, prefix="/api", tags=["Intelligence"])

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
        },
        status_code=200,
    )

@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "NeGD Digital Governance Intelligence API",
        "version": APP_VERSION,
        "docs": "/docs",   
        "health": "/health",
    }