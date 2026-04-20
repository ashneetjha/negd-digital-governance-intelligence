"""
Evaluation Service — Production-Grade RAG Quality Metrics

Computes 5 grounded metrics per RAG response:
  1. Keyword Match Score    = overlap(response_keywords, expected_keywords) / len(expected)
  2. Entity Consistency     = all expected entities appear in response
  3. Citation Density       = % of response sentences containing a citation marker
  4. Retrieval Hit          = at least 1 chunk with similarity >= 0.50
  5. Total Latency (ms)     = retrieval + LLM time

Returns an EvalMetrics dataclass attached to RAGResult and surfaced via ?debug=true.

Also exposes a module-level metrics accumulator for system health reporting.
"""

import re
import time
from dataclasses import dataclass, asdict
from typing import List, Optional
from collections import deque
from threading import Lock

# ─────────────────────────────────────────────────────────────────────────────
# Thresholds
# ─────────────────────────────────────────────────────────────────────────────

# Chunk classified as "relevant" if similarity >= this
_PRECISION_THRESHOLD: float = 0.30
# Chunk classified as "strong match" if similarity >= this
_RECALL_THRESHOLD: float = 0.50
# Citation regex: matches [Source N], [State | Month], or numbered references like [1], [2]
_CITATION_PATTERN = re.compile(
    r"\[Source\s*\d+\]|\[\w[\w\s]+\|[^\]]+\]|\[\d+\]",
    re.IGNORECASE,
)


# ─────────────────────────────────────────────────────────────────────────────
# EvalMetrics data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EvalMetrics:
    # Core metrics (always present)
    context_precision: float        # 0.0 – 1.0  (relevant_chunks / total)
    answer_faithfulness: bool       # True if response is grounded in context
    retrieval_recall: bool          # True if at least 1 strong-match chunk found
    total_latency_ms: float         # retrieval + LLM latency in ms
    chunks_total: int               # raw chunks after dedup
    chunks_relevant: int            # chunks above precision threshold

    # Extended metrics (populated when golden query keywords/entities are provided)
    keyword_match_score: float = 0.0    # 0.0 – 1.0
    entity_consistency: float = 0.0     # 0.0 – 1.0
    citation_density: float = 0.0       # 0.0 – 1.0  (% sentences with citation)
    retrieval_hit: float = 0.0          # 1.0 if strong match, 0.0 otherwise

    # Composite confidence (Task 3 formula)
    confidence_score: float = 0.0       # 0.0 – 1.0, weighted composite

    def to_dict(self) -> dict:
        return asdict(self)


# ─────────────────────────────────────────────────────────────────────────────
# Metric computation helpers
# ─────────────────────────────────────────────────────────────────────────────

def _compute_keyword_match(
    answer: str,
    expected_keywords: Optional[List[str]] = None,
) -> float:
    """
    Compute overlap ratio between expected keywords and response text.
    Returns 0.0 if no keywords provided.
    """
    if not expected_keywords:
        return 0.0
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return round(hits / len(expected_keywords), 4)


def _compute_entity_consistency(
    answer: str,
    expected_entities: Optional[List[str]] = None,
) -> float:
    """
    Check if all expected entities (state names, scheme names) appear in response.
    Returns 1.0 if all present, fractional if some missing, 0.0 if none.
    """
    if not expected_entities:
        return 1.0  # No entities to check → pass
    answer_lower = answer.lower()
    hits = sum(1 for e in expected_entities if e.lower() in answer_lower)
    return round(hits / len(expected_entities), 4)


def _compute_citation_density(answer: str) -> float:
    """
    Fraction of sentences in the response that contain at least one citation marker.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', answer) if s.strip()]
    if not sentences:
        return 0.0
    cited = sum(1 for s in sentences if _CITATION_PATTERN.search(s))
    return round(cited / len(sentences), 4)


def _compute_retrieval_hit(similarities: List[float]) -> float:
    """1.0 if any chunk has similarity >= RECALL_THRESHOLD, else 0.0."""
    return 1.0 if any(s >= _RECALL_THRESHOLD for s in similarities) else 0.0


def _compute_latency_penalty(total_latency_ms: float) -> float:
    """
    Latency penalty for confidence scoring.
    0.0 if ≤ 2000ms, scales linearly to 1.0 at 10000ms.
    """
    if total_latency_ms <= 2000:
        return 0.0
    if total_latency_ms >= 10000:
        return 1.0
    return round((total_latency_ms - 2000) / 8000, 4)


def compute_confidence(
    keyword_match: float,
    entity_consistency: float,
    citation_density: float,
    retrieval_hit: float,
    latency_penalty: float,
) -> float:
    """
    Task 3 — Composite confidence score.

    confidence = (
        keyword_match      * 0.25 +
        entity_consistency  * 0.25 +
        citation_density    * 0.20 +
        retrieval_hit       * 0.20 +
        (1 - latency_penalty) * 0.10
    )
    """
    return round(
        keyword_match * 0.25
        + entity_consistency * 0.25
        + citation_density * 0.20
        + retrieval_hit * 0.20
        + (1.0 - latency_penalty) * 0.10,
        4,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main evaluation function (called from rag_service.py)
# ─────────────────────────────────────────────────────────────────────────────

def evaluate_rag_response(
    similarities: List[float],
    faithfulness_passed: bool,
    retrieval_latency: float,
    llm_latency: float,
    answer: str = "",
    expected_keywords: Optional[List[str]] = None,
    expected_entities: Optional[List[str]] = None,
) -> EvalMetrics:
    """
    Compute all evaluation metrics for a single RAG response.

    Args:
        similarities:        Similarity scores for retrieved chunks.
        faithfulness_passed:  Whether the faithfulness check passed.
        retrieval_latency:   Retrieval time in seconds.
        llm_latency:         LLM inference time in seconds.
        answer:              The LLM-generated answer text (for citation density).
        expected_keywords:   Optional ground-truth keywords for scoring.
        expected_entities:   Optional expected entities for consistency check.

    Returns:
        EvalMetrics with all 5 metrics + composite confidence.
    """
    total = len(similarities)
    latency_ms = round((retrieval_latency + llm_latency) * 1000, 1)

    if total == 0:
        return EvalMetrics(
            context_precision=0.0,
            answer_faithfulness=faithfulness_passed,
            retrieval_recall=False,
            total_latency_ms=latency_ms,
            chunks_total=0,
            chunks_relevant=0,
            keyword_match_score=0.0,
            entity_consistency=0.0,
            citation_density=0.0,
            retrieval_hit=0.0,
            confidence_score=0.0,
        )

    relevant = [s for s in similarities if s >= _PRECISION_THRESHOLD]
    strong_match = any(s >= _RECALL_THRESHOLD for s in similarities)
    precision = round(len(relevant) / total, 4)

    # Extended metrics
    keyword_match = _compute_keyword_match(answer, expected_keywords)
    entity_consist = _compute_entity_consistency(answer, expected_entities)
    citation_dens = _compute_citation_density(answer)
    retrieval_hit = _compute_retrieval_hit(similarities)
    latency_penalty = _compute_latency_penalty(latency_ms)

    confidence = compute_confidence(
        keyword_match=keyword_match,
        entity_consistency=entity_consist,
        citation_density=citation_dens,
        retrieval_hit=retrieval_hit,
        latency_penalty=latency_penalty,
    )

    metrics = EvalMetrics(
        context_precision=precision,
        answer_faithfulness=faithfulness_passed,
        retrieval_recall=strong_match,
        total_latency_ms=latency_ms,
        chunks_total=total,
        chunks_relevant=len(relevant),
        keyword_match_score=keyword_match,
        entity_consistency=entity_consist,
        citation_density=citation_dens,
        retrieval_hit=retrieval_hit,
        confidence_score=confidence,
    )

    # Record for system health aggregation
    _record_metrics(metrics)

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# System Health Accumulator (Task 8)
# ─────────────────────────────────────────────────────────────────────────────
# Thread-safe rolling window of the last N query metrics.

_METRICS_WINDOW = 50
_metrics_lock = Lock()
_recent_metrics: deque = deque(maxlen=_METRICS_WINDOW)
_last_query_status: str = "none"
_last_query_ts: float = 0.0


def _record_metrics(m: EvalMetrics) -> None:
    global _last_query_status, _last_query_ts
    with _metrics_lock:
        _recent_metrics.append(m)
        _last_query_status = "ok"
        _last_query_ts = time.time()


def record_query_failure() -> None:
    """Call when a RAG query fails (from the route error handler)."""
    global _last_query_status, _last_query_ts
    with _metrics_lock:
        _last_query_status = "error"
        _last_query_ts = time.time()


def get_health_metrics() -> dict:
    """
    Return aggregated metrics for /api/system/status.
    """
    with _metrics_lock:
        if not _recent_metrics:
            return {
                "queries_tracked": 0,
                "avg_latency_ms": 0.0,
                "avg_confidence": 0.0,
                "avg_context_precision": 0.0,
                "avg_citation_density": 0.0,
                "success_rate": 0.0,
                "last_query_status": _last_query_status,
            }

        n = len(_recent_metrics)
        avg_lat = round(sum(m.total_latency_ms for m in _recent_metrics) / n, 1)
        avg_conf = round(sum(m.confidence_score for m in _recent_metrics) / n, 4)
        avg_prec = round(sum(m.context_precision for m in _recent_metrics) / n, 4)
        avg_cite = round(sum(m.citation_density for m in _recent_metrics) / n, 4)
        high_conf = sum(1 for m in _recent_metrics if m.confidence_score >= 0.4)
        success_rate = round(high_conf / n, 4)

        return {
            "queries_tracked": n,
            "avg_latency_ms": avg_lat,
            "avg_confidence": avg_conf,
            "avg_context_precision": avg_prec,
            "avg_citation_density": avg_cite,
            "success_rate": success_rate,
            "last_query_status": _last_query_status,
        }

