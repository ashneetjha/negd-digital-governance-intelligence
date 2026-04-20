"""
Insights Route — System-wide governance intelligence.

GET /api/insights/global   — Aggregated cross-state insights (no LLM call)
"""

from fastapi import APIRouter, HTTPException

from app.services.insight_service import generate_global_insights
from app.utils.logger import get_logger
from app.utils.response_formatter import build_intelligence_response

router = APIRouter()
logger = get_logger(__name__)


@router.get("/insights/global", tags=["Insights"])
async def global_insights():
    """
    Generate system-wide governance intelligence across all indexed states.
    Returns: top performing states, low adoption states, common gaps, emerging trends.
    No LLM call — purely rule-based from indexed data.
    """
    started = __import__("time").perf_counter()
    try:
        result = generate_global_insights()
        logger.info(
            "Global insights served",
            total_states=result.get("total_states", 0),
            status=result.get("status"),
        )
        answer = (
            f"Global governance insights generated for {result.get('total_states', 0)} states "
            f"from {result.get('total_reports', 0)} reports."
        )
        structured = {
            "summary": answer,
            "key_insights": [
                f"Top-performing states identified: {len(result.get('top_performing_states', []))}",
                f"Low-adoption states identified: {len(result.get('low_adoption_states', []))}",
                f"Emerging trends tracked: {len(result.get('emerging_trends', []))}",
            ],
            "changes_detected": result.get("emerging_trends", [])[:5],
            "risks": result.get("common_gaps", [])[:5],
            "status": "stable",
            "confidence": 0.85,
            "sources": [],
        }
        return build_intelligence_response(
            answer=answer,
            structured=structured,
            sources=[],
            metadata={
                "route": "rag",
                "status": result.get("status", "ok"),
                "total_states": result.get("total_states", 0),
                "total_reports": result.get("total_reports", 0),
                "confidence": 0.85,
                "latency": round((__import__("time").perf_counter() - started) * 1000, 2),
            },
            data=result,
        )
    except Exception as exc:
        logger.error("Global insights error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal insights error.")
