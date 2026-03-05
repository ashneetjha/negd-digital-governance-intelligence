"""
NeGD Digital Governance Intelligence Portal
FastAPI Backend — Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json

from app.config import settings
from app.routes import ingest, analysis, compare, reports, system
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

# Ensure allowed_origins is always a list, even if passed as a string from Render
raw_origins = settings.ALLOWED_ORIGINS
if isinstance(raw_origins, str):
    try:
        allowed_origins = json.loads(raw_origins)
    except json.JSONDecodeError:
        allowed_origins = [raw_origins]
else:
    allowed_origins = raw_origins or ["http://localhost:3000"]

# Add your production Netlify URL explicitly to ensure access
production_url = "https://negd-digital-governance-intelligence.netlify.app"
if production_url not in allowed_origins:
    allowed_origins.append(production_url)

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
    )


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