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

from app.services.comparison_service import run_comparison, compare_cross_state
from app.utils.logger import get_logger
from app.utils.response_formatter import build_intelligence_response

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

    started = __import__("time").perf_counter()
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
        structured = {
            "summary": result.get("summary", "Comparison completed."),
            "key_insights": result.get("new_initiatives", [])[:5],
            "changes_detected": result.get("quantitative_changes", []) + result.get("compliance_changes", []),
            "risks": result.get("removed_mentions", [])[:5],
            "status": "stable" if not result.get("new_initiatives") else "improved",
            "confidence": float(result.get("confidence", 0.0) or 0.0),
            "sources": result.get("citations", []),
        }
        return build_intelligence_response(
            answer=structured["summary"],
            structured=structured,
            sources=result.get("citations", []),
            metadata={
                "route": "comparison",
                "status": result.get("status", "ok"),
                "state": request.state,
                "month_a": request.month_a,
                "month_b": request.month_b,
                "confidence": result.get("confidence", 0.0),
                "latency": round((__import__("time").perf_counter() - started) * 1000, 2),
            },
            data=result,
        )
    except RuntimeError as exc:
        message = str(exc)
        logger.warning("Comparison degraded fallback", error=message)
        fallback = "Comparison is temporarily unavailable in full mode. Returning safe fallback response."
        return build_intelligence_response(
            answer=fallback,
            structured={
                "summary": fallback,
                "key_insights": ["Try again in a few minutes once AI dependencies recover."],
                "changes_detected": [],
                "risks": ["Temporary AI dependency issue"],
                "status": "limited",
                "confidence": 0.0,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "comparison",
                "status": "fallback",
                "state": request.state,
                "month_a": request.month_a,
                "month_b": request.month_b,
                "confidence": 0.0,
                "latency": round((__import__("time").perf_counter() - started) * 1000, 2),
                "error": message,
            },
            data={"status": "fallback", "error": message},
        )
    except Exception as exc:
        logger.error("Comparison error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal comparison error.")


# ── Cross-State Comparison ─────────────────────────────────────

class CrossStateRequest(BaseModel):
    state_a: str
    month_a: str
    state_b: str
    month_b: str
    topic: Optional[str] = None


@router.post("/compare/cross-state")
async def compare_cross_state_endpoint(request: CrossStateRequest):
    """
    Compare governance reporting between TWO DIFFERENT STATES.
    Produces: strengths per state, common initiatives, adoption comparison,
    performance gaps, recommendations, and citations.
    """
    if request.state_a.strip().lower() == request.state_b.strip().lower() and request.month_a == request.month_b:
        raise HTTPException(
            status_code=400,
            detail="For same state and same month, use /api/compare instead.",
        )

    started = __import__("time").perf_counter()
    try:
        result = compare_cross_state(
            state_a=request.state_a,
            month_a=request.month_a,
            state_b=request.state_b,
            month_b=request.month_b,
            topic=request.topic,
        )
        logger.info(
            "Cross-state comparison served",
            state_a=request.state_a,
            month_a=request.month_a,
            state_b=request.state_b,
            month_b=request.month_b,
        )
        structured = {
            "summary": result.get("summary", "Cross-state comparison completed."),
            "key_insights": result.get("commonalities", [])[:5],
            "changes_detected": result.get("differences", [])[:7],
            "risks": result.get("performance_gaps", [])[:5],
            "status": "stable" if not result.get("differences") else "improved",
            "confidence": float(result.get("confidence", 0.0) or 0.0),
            "sources": result.get("citations", []),
        }
        return build_intelligence_response(
            answer=structured["summary"],
            structured=structured,
            sources=result.get("citations", []),
            metadata={
                "route": "cross_state",
                "status": result.get("status", "ok"),
                "state_a": request.state_a,
                "month_a": request.month_a,
                "state_b": request.state_b,
                "month_b": request.month_b,
                "confidence": result.get("confidence", 0.0),
                "latency": round((__import__("time").perf_counter() - started) * 1000, 2),
            },
            data=result,
        )
    except RuntimeError as exc:
        message = str(exc)
        logger.warning("Cross-state comparison degraded fallback", error=message)
        fallback = "Cross-state comparison is temporarily unavailable in full mode. Returning safe fallback response."
        return build_intelligence_response(
            answer=fallback,
            structured={
                "summary": fallback,
                "key_insights": ["Retry once AI dependencies are available."],
                "changes_detected": [],
                "risks": ["Temporary AI dependency issue"],
                "status": "limited",
                "confidence": 0.0,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "cross_state",
                "status": "fallback",
                "state_a": request.state_a,
                "month_a": request.month_a,
                "state_b": request.state_b,
                "month_b": request.month_b,
                "confidence": 0.0,
                "latency": round((__import__("time").perf_counter() - started) * 1000, 2),
                "error": message,
            },
            data={"status": "fallback", "error": message},
        )
    except Exception as exc:
        logger.error("Cross-state comparison error", error=str(exc))
        raise HTTPException(status_code=500, detail="Internal cross-state comparison error.")
