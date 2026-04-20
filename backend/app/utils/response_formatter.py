"""Helpers for stable API response envelopes across intelligence endpoints."""

from typing import Any


def _primary_source(sources: list[Any]) -> str:
    if not sources:
        return "System Aggregated Data"

    first = sources[0]
    if isinstance(first, dict):
        state = first.get("state") or "Unknown State"
        month = first.get("month") or first.get("reporting_month") or "Unknown Month"
        return f"{state} - {month}"

    state = getattr(first, "state", None) or "Unknown State"
    month = getattr(first, "month", None) or getattr(first, "reporting_month", None) or "Unknown Month"
    return f"{state} - {month}"


def _justification(answer: str, structured: dict[str, Any], metadata: dict[str, Any]) -> str:
    if isinstance(structured.get("summary"), str) and structured.get("summary"):
        return str(structured["summary"])
    if isinstance(metadata.get("confidence_explanation"), str) and metadata.get("confidence_explanation"):
        return str(metadata["confidence_explanation"])
    return answer[:240] if answer else "Response generated from available indexed governance evidence."


def build_intelligence_response(
    *,
    answer: str,
    structured: dict[str, Any] | None = None,
    sources: list[Any] | None = None,
    metadata: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    # New canonical fields
    top_insights: list[str] | None = None,
    gaps: list[dict[str, Any]] | None = None,
    recommendations: list[dict[str, Any]] | None = None,
    ranking: list[dict[str, Any]] | None = None,
    confidence_reason: str | None = None,
) -> dict[str, Any]:
    """
    Return a stable, fully-specified response envelope.

    Canonical top-level fields (always present):
      - answer
      - top_insights
      - gaps
      - recommendations
      - ranking
      - confidence
      - confidence_reason
      - source
      - justification
      - structured  (legacy / per-endpoint details)
      - sources     (citation list)
      - metadata    (route, latency, etc.)
      - data        (full raw payload for consumers that need it)
    """
    canonical_answer = answer or ""
    canonical_structured = structured or {}
    canonical_sources = sources or []
    canonical_metadata = dict(metadata or {})
    canonical_metadata.setdefault("route", "rag")
    canonical_metadata.setdefault("confidence", 0.0)
    canonical_metadata.setdefault("latency", 0.0)

    canonical_confidence = float(canonical_metadata.get("confidence", 0.0) or 0.0)
    canonical_source = _primary_source(canonical_sources)
    canonical_justification = _justification(canonical_answer, canonical_structured, canonical_metadata)

    # Derive top_insights from structured if not supplied
    if top_insights is None:
        raw_insights = canonical_structured.get("key_insights", [])
        top_insights = [str(i) for i in raw_insights if i][:5]

    canonical_top_insights = top_insights or []
    canonical_gaps = gaps or []
    canonical_recommendations = recommendations or []
    canonical_ranking = ranking or []
    canonical_confidence_reason = (
        confidence_reason
        or canonical_metadata.get("confidence_reason", "")
        or ""
    )

    payload_data = dict(data or {})
    payload_data.setdefault("answer", canonical_answer)
    payload_data.setdefault("structured", canonical_structured)
    payload_data.setdefault("sources", canonical_sources)
    payload_data.setdefault("metadata", canonical_metadata)
    payload_data.setdefault("confidence", canonical_confidence)
    payload_data.setdefault("source", canonical_source)
    payload_data.setdefault("justification", canonical_justification)
    payload_data.setdefault("top_insights", canonical_top_insights)
    payload_data.setdefault("gaps", canonical_gaps)
    payload_data.setdefault("recommendations", canonical_recommendations)
    payload_data.setdefault("ranking", canonical_ranking)
    payload_data.setdefault("confidence_reason", canonical_confidence_reason)

    return {
        # Core answer
        "answer": canonical_answer,
        # Structured intelligence fields (new canonical spec)
        "top_insights": canonical_top_insights,
        "gaps": canonical_gaps,
        "recommendations": canonical_recommendations,
        "ranking": canonical_ranking,
        "confidence": canonical_confidence,
        "confidence_reason": canonical_confidence_reason,
        "source": canonical_source,
        "justification": canonical_justification,
        # Supporting data
        "structured": canonical_structured,
        "sources": canonical_sources,
        "metadata": canonical_metadata,
        # Full raw payload
        "data": payload_data,
        # Compatibility shim
        "success": True,
    }
