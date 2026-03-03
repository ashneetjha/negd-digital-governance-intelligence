"""
System diagnostics route.

GET /api/system/status
"""

import time
from typing import Any

import httpx
from fastapi import APIRouter

from app.config import settings
from app.db.database import get_supabase
from app.services.embedding_service import _load_model
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _empty_embedding_vector() -> list[float]:
    return [0.0] * int(settings.EMBEDDING_DIMENSION)


@router.get("/system/status")
async def get_system_status() -> dict[str, Any]:
    started = time.perf_counter()

    payload: dict[str, Any] = {
        "backend": {
            "status": "ok",
            "version": "1.0.0",
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

    # Embedding model probe
    try:
        model = _load_model()
        payload["embedding"]["loaded"] = model is not None
        if model is None and settings.STRICT_REAL_AI:
            payload["embedding"]["error"] = "Embedding model missing in strict mode."
    except Exception as exc:
        payload["embedding"]["error"] = str(exc)

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
    )
    return payload

