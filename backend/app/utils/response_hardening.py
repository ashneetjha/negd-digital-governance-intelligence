"""
Response Hardening — Ensure NEVER empty, timeout-safe responses

All endpoints must:
  1. ALWAYS return an answer (never empty)
  2. ALWAYS include confidence + trust metadata
  3. ALWAYS include fallback data if no real data available
  4. ALWAYS be resilient to timeout/API failures
"""

from typing import Dict, Any, Optional


def safe_wrap_response(
    answer: Optional[str] = None,
    structured: Optional[Dict[str, Any]] = None,
    sources: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    status: str = "ok",
    confidence: float = 0.0,
) -> Dict[str, Any]:
    """
    Wrap response with hardened defaults to ensure NEVER empty responses.
    
    Guarantees:
    - answer is never empty/None
    - confidence is always present
    - status always indicates readiness
    - metadata always has route, confidence, latency
    """
    
    canonical_answer = (answer or "").strip()
    if not canonical_answer:
        canonical_answer = "System processed your query. Limited information available for detailed analysis."
    
    canonical_structured = structured or {
        "summary": canonical_answer,
        "key_insights": [],
        "changes_detected": [],
        "risks": [],
        "status": "limited",
        "confidence": confidence,
        "sources": [],
    }
    
    canonical_sources = sources or []
    
    canonical_metadata = dict(metadata or {})
    canonical_metadata.setdefault("route", "standard")
    canonical_metadata.setdefault("confidence", round(max(0.0, min(confidence, 1.0)), 4))
    canonical_metadata.setdefault("latency", 0.0)
    canonical_metadata.setdefault("status", status)
    canonical_metadata.setdefault("fallback", confidence < 0.3)
    
    payload_data = dict(data or {})
    payload_data.setdefault("answer", canonical_answer)
    payload_data.setdefault("structured", canonical_structured)
    payload_data.setdefault("sources", canonical_sources)
    payload_data.setdefault("metadata", canonical_metadata)
    
    return {
        "success": True,
        "answer": canonical_answer,
        "structured": canonical_structured,
        "sources": canonical_sources,
        "metadata": canonical_metadata,
        "data": payload_data,
    }


def safe_fallback_response(
    query: str,
    reason: str = "System unavailable",
    route: str = "fallback",
) -> Dict[str, Any]:
    """
    Safe fallback response when all pipelines fail.
    
    Ensures:
    - Always returns valid response
    - Acknowledges limitation transparently
    - Does not fail silently
    """
    
    fallback_answer = (
        f"I was unable to process your query  in detail due to: {reason}. "
        f"Your query was: \"{query[:100]}...\" "
        f"Please try again or contact support if this issue persists."
    )
    
    return safe_wrap_response(
        answer=fallback_answer,
        structured={
            "summary": "System temporarily unavailable for detailed analysis",
            "key_insights": ["System is operating in limited mode"],
            "changes_detected": [],
            "risks": [reason],
            "status": "limited",
            "confidence": 0.0,
            "sources": [],
        },
        sources=[],
        metadata={
            "route": route,
            "confidence": 0.0,
            "latency": 0.0,
            "status": "fallback",
            "fallback": True,
            "reason": reason,
        },
        status="fallback",
        confidence=0.0,
    )


def add_confidence_trust_metadata(
    response: Dict[str, Any],
    confidence: float,
    source_count: int,
    avg_similarity: float,
) -> Dict[str, Any]:
    """
    Enhance response with detailed confidence + trust reasoning.
    """
    
    # Build confidence explanation
    reasons = []
    if source_count >= 3:
        reasons.append(f"grounded in {source_count} reliable sources")
    elif source_count > 0:
        reasons.append(f"based on {source_count} source(s)")
    else:
        reasons.append("limited source evidence")
    
    if avg_similarity >= 0.6:
        reasons.append("high relevance match")
    elif avg_similarity >= 0.4:
        reasons.append("moderate relevance")
    else:
        reasons.append("loose match (caution advised)")
    
    confidence_explanation = f"HIGH confidence: {', '.join(reasons)}." if confidence >= 0.7 else \
                            f"MODERATE confidence: {', '.join(reasons)}." if confidence >= 0.5 else \
                            f"LIMITED confidence: {', '.join(reasons)}."
    
    # Update metadata
    if "metadata" in response:
        response["metadata"]["confidence_explanation"] = confidence_explanation
        response["metadata"]["trust_score"] = round(confidence * 100)
    
    if "structured" in response:
        response["structured"]["confidence"] = round(confidence, 4)
    
    return response
