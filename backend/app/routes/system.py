"""
System diagnostics route.

GET /api/ping          — ultra-lightweight keep-alive (no DB / model calls)
GET /api/system/status — full diagnostic probe + RAG health metrics
"""

import time
from typing import Any

import httpx
from fastapi import APIRouter

from app.config import settings
from app.db.database import get_supabase
from app.services.embedding_service import get_embedding_status
from app.services.evaluation_service import get_health_metrics
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────
# Lightweight ping — designed for UptimeRobot / cron-job.org
# and for the frontend BackendWakeup component.
# No database or AI model calls; always responds in < 5 ms.
# ──────────────────────────────────────────────────────────────

@router.get("/ping", tags=["System"])
async def ping():
    return {
        "pong": True,
        "ts": time.time(),
        "service": "negd-digital-governance-intelligence-api",
    }


def _empty_embedding_vector() -> list[float]:
    return [0.0] * int(settings.EMBEDDING_DIMENSION)


@router.get("/system/status")
async def get_system_status() -> dict[str, Any]:
    started = time.perf_counter()

    payload: dict[str, Any] = {
        "backend": {
            "status": "ok",
            "version": "3.0.0",
            "environment": settings.APP_ENV,
        },
        "supabase": {
            "configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
            "reachable": False,
            "table_probe": False,
            "rpc_probe": False,
            "error": None,
        },
        "embedding": {
            "model": settings.EMBEDDING_MODEL,
            "loaded": False,
            "error": None,
        },
        "groq": {
            "configured": bool(settings.GROQ_API_KEY),
            "reachable": False,
            "model": settings.GROQ_MODEL,
            "error": None,
        },
        "strict_ai_mode": settings.STRICT_REAL_AI,
    }

    # Supabase probe
    try:
        supabase = get_supabase()
        _ = supabase.table("reports").select("id").limit(1).execute()
        payload["supabase"]["table_probe"] = True

        rpc = supabase.rpc(
            "match_chunks",
            {
                "query_embedding": _empty_embedding_vector(),
                "filter_state": None,
                "filter_month": None,
                "filter_section": None,
                "match_count": 1,
            },
        ).execute()
        _ = rpc.data
        payload["supabase"]["rpc_probe"] = True
        payload["supabase"]["reachable"] = True
    except Exception as exc:
        payload["supabase"]["error"] = str(exc)

    # Embedding model probe — non-blocking; reports current load state
    emb_status = get_embedding_status()
    payload["embedding"]["loaded"] = emb_status["loaded"]
    payload["embedding"]["boot_status"] = emb_status["status"]
    payload["embedding"]["mode"] = emb_status.get("mode", "unknown")
    if emb_status["error"]:
        payload["embedding"]["error"] = emb_status["error"]
    elif emb_status["status"] == "loading":
        payload["embedding"]["error"] = "Model is warming up — retry in a few seconds."

    # Groq probe
    if payload["groq"]["configured"]:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                )
            payload["groq"]["reachable"] = res.status_code == 200
            if res.status_code != 200:
                payload["groq"]["error"] = f"Groq HTTP {res.status_code}"
        except Exception as exc:
            payload["groq"]["error"] = str(exc)
    else:
        payload["groq"]["error"] = "GROQ_API_KEY not configured."

    # ── Task 8: RAG Health Metrics ────────────────────────────────────────────
    rag_health_metrics = get_health_metrics()
    payload["rag_health"] = {
        "status": "healthy" if rag_health_metrics["last_query_status"] != "error" else "degraded",
        "queries_tracked": rag_health_metrics["queries_tracked"],
        "avg_latency_ms": rag_health_metrics["avg_latency_ms"],
        "avg_confidence": rag_health_metrics["avg_confidence"],
        "avg_context_precision": rag_health_metrics["avg_context_precision"],
        "avg_citation_density": rag_health_metrics["avg_citation_density"],
        "success_rate": rag_health_metrics["success_rate"],
        "last_query_status": rag_health_metrics["last_query_status"],
    }
    payload["embedding_mode"] = emb_status.get("mode", "unknown")

    # Determine overall health
    strict_ok = (
        payload["supabase"]["reachable"]
        and payload["embedding"]["loaded"]
        and payload["groq"]["reachable"]
    )
    relaxed_ok = payload["supabase"]["reachable"]
    healthy = strict_ok if settings.STRICT_REAL_AI else relaxed_ok
    payload["overall_status"] = "healthy" if healthy else "degraded"
    payload["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)

    logger.info(
        "System status served",
        overall_status=payload["overall_status"],
        strict_mode=settings.STRICT_REAL_AI,
        latency_ms=payload["latency_ms"],
        rag_queries=rag_health_metrics["queries_tracked"],
        avg_confidence=rag_health_metrics["avg_confidence"],
    )
    return payload
