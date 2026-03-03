"""
NeGD Digital Governance Intelligence Portal
FastAPI Backend — Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
# CORS Configuration
# ──────────────────────────────────────────────────────────────

allowed_origins = settings.ALLOWED_ORIGINS or ["http://localhost:3000"]

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
