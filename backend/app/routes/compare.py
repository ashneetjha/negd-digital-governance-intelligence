"""
Compare Route — Month-to-month governance comparison.

POST /api/compare
  - state: str
  - month_a: str (YYYY-MM)
  - month_b: str (YYYY-MM)
  - topic: Optional[str]
"""
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.comparison_service import run_comparison
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class CompareRequest(BaseModel):
    state: str
    month_a: str
    month_b: str
    topic: Optional[str] = None


@router.post("/compare")
async def compare_months(request: CompareRequest):
    """
    Compare governance reporting for a state across two months.
    Returns structured diff: new initiatives, removed mentions, 
    quantitative changes, compliance changes, and citations.
    """
    if request.month_a == request.month_b:
        raise HTTPException(status_code=400, detail="month_a and month_b must be different.")

    try:
        result = run_comparison(
            state=request.state,
            month_a=request.month_a,
            month_b=request.month_b,
            topic=request.topic,
        )
        logger.info(
            "Comparison served",
            state=request.state,
            month_a=request.month_a,
            month_b=request.month_b,
        )
        return {"success": True, "data": result}
    except RuntimeError as exc:
        message = str(exc)
        if "GROQ_API_KEY" in message:
            raise HTTPException(
                status_code=503,
                detail={"code": "AI_NOT_CONFIGURED", "message": "AI service not configured."},
            )
        if "STRICT_REAL_AI" in message or "Embedding model unavailable" in message:
            raise HTTPException(
                status_code=503,
                detail={
                    "code": "EMBEDDING_DEPENDENCY_UNAVAILABLE",
                    "message": "Embedding dependency unavailable in strict AI mode.",
                },
            )
        raise HTTPException(
            status_code=503,
            detail={"code": "AI_DEPENDENCY_UNAVAILABLE", "message": message},
        )
    except Exception as exc:
        logger.error("Comparison error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal comparison error.")
