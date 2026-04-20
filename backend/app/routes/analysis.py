"""
Analysis Route — Multi-layer orchestration entrypoint.

POST /api/analysis
  - prompt: str
  - state: Optional[str]
  - month: Optional[str]

Routing result: chat | rag | comparison | cross_state
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.chat_service import run_chat
from app.services.evaluation_service import record_query_failure
from app.services.rag_service import run_rag
from app.services.router_service import classify_route
from app.utils.logger import get_logger
from app.utils.response_formatter import build_intelligence_response

router = APIRouter()
logger = get_logger(__name__)


class AnalysisRequest(BaseModel):
    prompt: Optional[str] = None
    query: Optional[str] = None
    state: Optional[str] = None
    month: Optional[str] = None


def _structured_from_comparison(result: dict) -> dict:
    return {
        "summary": result.get("summary", "Comparison completed."),
        "key_insights": result.get("commonalities")
        or result.get("differences", [])[:5]
        or result.get("new_initiatives", [])[:5],
        "changes_detected": result.get("differences")
        or result.get("quantitative_changes", [])
        or result.get("compliance_changes", []),
        "risks": result.get("performance_gaps", []),
        "status": "stable" if not result.get("differences") else "improved",
        "confidence": float(result.get("confidence", 0.5) or 0.5),
        "sources": result.get("citations", []),
    }


def _structured_from_insights(answer: str, confidence: float) -> dict:
    return {
        "summary": answer,
        "key_insights": [line.strip() for line in answer.split("\n") if line.strip()][:5],
        "changes_detected": [],
        "risks": [],
        "status": "stable",
        "confidence": confidence,
        "sources": [],
    }


def _handle_cross_state_route(prompt: str, entities: dict, state: Optional[str]) -> Optional[dict]:
    from app.services.comparison_service import compare_cross_state

    states = entities.get("states", []) or []
    months = entities.get("months", []) or []

    if state and state not in states:
        states.insert(0, state)

    if len(states) < 2:
        return None

    month_a = months[0] if len(months) >= 1 else "latest"
    month_b = months[1] if len(months) >= 2 else month_a

    result = compare_cross_state(
        state_a=states[0],
        month_a=month_a,
        state_b=states[1],
        month_b=month_b,
        topic=prompt,
    )

    structured = _structured_from_comparison(result)
    return build_intelligence_response(
        answer=structured["summary"],
        structured=structured,
        sources=result.get("citations", []),
        metadata={
            "route": "cross_state",
            "confidence": structured["confidence"],
            "latency": 0,
            "status": result.get("status", "ok"),
        },
        data={
            "answer": structured["summary"],
            "structured": structured,
            "citations": result.get("citations", []),
            "comparison_data": result,
            "routed_to": "cross_state",
            "confidence": structured["confidence"],
        },
    )


def _handle_month_comparison_route(prompt: str, entities: dict, state: Optional[str], month: Optional[str]) -> Optional[dict]:
    from app.services.comparison_service import run_comparison

    states = entities.get("states", []) or []
    months = entities.get("months", []) or []

    chosen_state = state or (states[0] if states else None)
    if not chosen_state:
        return None

    if month and month not in months:
        months = [month] + months

    if len(months) < 2:
        # insufficient explicit months; route should safely fall back to rag
        return None

    result = run_comparison(
        state=chosen_state,
        month_a=months[0],
        month_b=months[1],
        topic=prompt,
    )

    structured = _structured_from_comparison(result)
    return build_intelligence_response(
        answer=structured["summary"],
        structured=structured,
        sources=result.get("citations", []),
        metadata={
            "route": "comparison",
            "confidence": structured["confidence"],
            "latency": 0,
            "status": result.get("status", "ok"),
        },
        data={
            "answer": structured["summary"],
            "structured": structured,
            "citations": result.get("citations", []),
            "comparison_data": result,
            "routed_to": "comparison",
            "confidence": structured["confidence"],
        },
    )


@router.post("/analysis")
async def run_analysis(
    request: AnalysisRequest,
    debug: bool = Query(default=False, description="Set true to include evaluation metrics in the response"),
):
    try:
        prompt_val = request.prompt or request.query
        if not prompt_val or not prompt_val.strip():
            raise ValueError("Prompt missing")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if len(prompt_val) > 2000:
        raise HTTPException(status_code=400, detail="Prompt exceeds 2000 character limit.")
    request.prompt = prompt_val

    started = time.perf_counter()
    decision = classify_route(
        request.prompt,
        explicit_state=request.state,
        explicit_month=request.month,
    )

    try:
        if decision.route == "chat":
            chat_result = run_chat(message=request.prompt, history=None)
            latency = round((time.perf_counter() - started) * 1000, 2)
            return build_intelligence_response(
                answer=chat_result.get("answer", ""),
                structured={
                    "summary": chat_result.get("answer", ""),
                    "key_insights": [],
                    "changes_detected": [],
                    "risks": [],
                    "status": "stable",
                    "confidence": decision.confidence,
                    "sources": chat_result.get("sources", []),
                },
                sources=chat_result.get("sources", []),
                metadata={
                    "route": "chat",
                    "confidence": decision.confidence,
                    "latency": latency,
                    "router": {
                        "rationale": decision.rationale,
                        "model_used": decision.model_used,
                        "entities": decision.entities,
                    },
                },
                data={
                    "answer": chat_result.get("answer", ""),
                    "sources": chat_result.get("sources", []),
                    "metadata": chat_result.get("metadata", {}),
                    "routed_to": "chat",
                },
            )

        if decision.route == "cross_state":
            routed = _handle_cross_state_route(request.prompt, decision.entities, request.state)
            if routed:
                routed["metadata"]["latency"] = round((time.perf_counter() - started) * 1000, 2)
                routed["metadata"]["router"] = {
                    "rationale": decision.rationale,
                    "model_used": decision.model_used,
                    "entities": decision.entities,
                }
                return routed

        if decision.route == "comparison":
            routed = _handle_month_comparison_route(
                request.prompt,
                decision.entities,
                request.state,
                request.month,
            )
            if routed:
                routed["metadata"]["latency"] = round((time.perf_counter() - started) * 1000, 2)
                routed["metadata"]["router"] = {
                    "rationale": decision.rationale,
                    "model_used": decision.model_used,
                    "entities": decision.entities,
                }
                return routed

        # Default and fallback route: RAG
        result = run_rag(
            prompt=request.prompt,
            state=request.state,
            month=request.month,
            entities=decision.entities,
        )
        response_data = result.to_dict(include_eval=debug)
        response_data["routed_to"] = "rag"

        rag_confidence_reason = response_data.get("confidence_reason", "")
        latency = round((time.perf_counter() - started) * 1000, 2)
        return build_intelligence_response(
            answer=response_data.get("answer", ""),
            structured=response_data.get("structured", {}),
            sources=response_data.get("citations", response_data.get("sources", [])),
            confidence_reason=rag_confidence_reason,
            metadata={
                "route": "rag",
                "confidence": response_data.get("confidence", response_data.get("confidence_score", 0.0)),
                "confidence_reason": rag_confidence_reason,
                "latency": latency,
                "status": response_data.get("status", "ok"),
                "retrieval_method": response_data.get("retrieval_method", "hybrid"),
                "router": {
                    "rationale": decision.rationale,
                    "model_used": decision.model_used,
                    "entities": decision.entities,
                },
            },
            data=response_data,
        )

    except RuntimeError as exc:
        record_query_failure()
        message = str(exc)
        logger.warning("Analysis degraded fallback", error=message)
        fallback_answer = (
            "Analysis is running in degraded mode due to a temporary AI dependency issue. "
            "Returning a safe partial response based on currently available metadata."
        )
        return build_intelligence_response(
            answer=fallback_answer,
            structured={
                "summary": fallback_answer,
                "key_insights": [
                    "Primary analysis model is temporarily unavailable.",
                    "Retrying shortly should restore full evidence-grounded analysis.",
                ],
                "changes_detected": [],
                "risks": ["Temporary AI dependency issue"],
                "status": "limited",
                "confidence": 0.0,
                "sources": [],
            },
            sources=[],
            metadata={
                "route": "rag",
                "confidence": 0.0,
                "latency": round((time.perf_counter() - started) * 1000, 2),
                "status": "fallback",
                "error": message,
            },
            data={"routed_to": "rag", "status": "fallback", "error": message},
        )
    except Exception as exc:
        record_query_failure()
        logger.error("Analysis error", error=str(exc))
        error_msg = str(exc)
        return build_intelligence_response(
            answer="Internal analysis error occurred.",
            structured={
                "summary": "Internal analysis error occurred.",
                "key_insights": [],
                "changes_detected": [],
                "risks": [],
                "status": "error",
                "confidence": 0.0,
                "sources": [],
                "error": True,
                "error_type": "INTERNAL_ERROR",
                "message": "Internal analysis error.",
                "details": error_msg,
                "fallback_used": False,
            },
            sources=[],
            metadata={
                "route": "error",
                "confidence": 0.0,
                "latency": round((time.perf_counter() - started) * 1000, 2),
                "status": "error",
                "error": True,
                "error_type": "INTERNAL_ERROR",
                "message": "Internal analysis error.",
                "details": error_msg,
                "fallback_used": False,
            },
            data={
                "routed_to": "error",
                "status": "error",
                "error": True,
                "error_type": "INTERNAL_ERROR",
                "message": "Internal analysis error.",
                "details": error_msg,
                "fallback_used": False,
            }
        )
