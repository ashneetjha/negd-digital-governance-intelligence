"""
RAG Service — Hybrid Multi-Stage Retrieval-Augmented Generation (v3.0)
Thin Orchestrator
"""

import time
from typing import Optional
from statistics import mean
from groq import Groq

from app.config import settings
from app.services.evaluation_service import (
    evaluate_rag_response,
    record_query_failure,
)
from app.services.verification_service import verify_response
from app.services.analysis_layer import (
    extract_key_facts,
    comparative_analysis,
    synthesize_insights,
    build_confidence_explanation,
)
from app.utils.logger import get_logger

from app.services.models import RAGResult
from app.services.cache_service import get_cache_key, get_from_cache, set_in_cache
from app.services.query_service import normalize_query, rewrite_query
from app.services.metadata_service import extract_query_metadata
from app.services.retrieval_service import (
    multi_pass_retrieval, bm25_search, fuse_results, rank_with_metadata
)
from app.services.reranker_service import rerank_with_cross_encoder, rerank_diverse
from app.services.context_service import (
    build_context, get_system_prompt, LOW_CONTEXT_SYSTEM_PROMPT, SIMILARITY_THRESHOLD
)
from app.services.llm_service import (
    generate_answer, generate_structured_output, extract_key_points, faithfulness_check
)
from app.services.confidence_service import calculate_final_confidence, determine_status

logger = get_logger(__name__)

# ==========================================================
# THRESHOLDS
# ==========================================================
_NOISE_FLOOR: float = 0.05


def _error_payload(error_type: str, message: str, details: str, fallback_used: bool) -> dict:
    return {
        "error": True,
        "error_type": error_type,
        "message": message,
        "details": details,
        "fallback_used": fallback_used,
    }


def _build_rag_error_result(
    answer: str,
    retrieval_latency: float,
    query_rewritten: bool,
    retrieval_method: str,
    details: str,
    error_type: str,
    confidence_reason: str,
    justification: str,
) -> RAGResult:
    error_info = _error_payload(error_type, answer, details, True)
    result = RAGResult(
        answer=answer,
        sources=[],
        chunks_retrieved=0,
        confidence_score=0.0,
        retrieval_quality=0.0,
        hallucination_risk=1.0 if error_type == "LLM_ERROR" else 0.0,
        retrieval_latency=retrieval_latency,
        llm_latency=0.0,
        tokens_used=0,
        context_truncated=False,
        faithfulness_passed=False if error_type == "LLM_ERROR" else True,
        cache_hit=False,
        status="error" if error_type != "NO_DATA" else "no_data",
        mode="strict",
        retrieval_method=retrieval_method,
        query_rewritten=query_rewritten,
        structured={
            "summary": answer,
            "key_insights": [],
            "changes_detected": [],
            "risks": [details or justification],
            "status": "limited",
            "confidence": 0.0,
            "sources": [],
            "top_insights": [],
            "gaps": [],
            "recommendations": [],
            "confidence_reason": confidence_reason,
            "justification": justification,
            **error_info,
        },
        error=error_info["error"],
        error_type=error_info["error_type"],
        message=error_info["message"],
        details=error_info["details"],
        fallback_used=error_info["fallback_used"],
    )
    result.confidence_reason = confidence_reason
    result.data_coverage = "limited"
    return result


def _build_no_data_result(
    retrieval_latency: float,
    query_rewritten: bool,
    retrieval_method: str,
    reason: str,
) -> RAGResult:
    """Return a strict no_data response when retrieval yields nothing.
    NEVER hallucinate — this is the authoritative empty-retrieval response.
    """
    answer = "No data available for selected filters."
    result = RAGResult(
        answer=answer,
        sources=[],
        chunks_retrieved=0,
        confidence_score=0.0,
        retrieval_quality=0.0,
        hallucination_risk=0.0,
        retrieval_latency=retrieval_latency,
        llm_latency=0.0,
        tokens_used=0,
        context_truncated=False,
        faithfulness_passed=True,
        cache_hit=False,
        status="no_data",
        mode="strict",
        retrieval_method=retrieval_method,
        query_rewritten=query_rewritten,
        structured={
            "summary": answer,
            "key_insights": [],
            "changes_detected": [],
            "risks": [],
            "status": "no_data",
            "confidence": 0.0,
            "sources": [],
            "top_insights": [],
            "gaps": [],
            "recommendations": [],
            "confidence_reason": reason,
            "justification": reason,
            "error": True,
        },
        error=True,
        error_type="NO_DATA",
        message=answer,
        details=reason,
        fallback_used=False,
    )
    result.confidence_reason = reason
    result.data_coverage = "none"
    return result

# ==========================================================
# MAIN PIPELINE
# ==========================================================

def run_rag(prompt: str, state=None, month=None, section=None, entities: Optional[dict] = None):

    pipeline_started = time.perf_counter()

    normalized_prompt = normalize_query(prompt)
    if not settings.GROQ_API_KEY:
        return _build_rag_error_result(
            answer="System temporarily unable to generate response.",
            retrieval_latency=0.0,
            query_rewritten=False,
            retrieval_method="error",
            details="GROQ_API_KEY is not configured.",
            error_type="LLM_ERROR",
            confidence_reason="No data available",
            justification="LLM service is not configured.",
        )

    cache_key = get_cache_key(normalized_prompt, state, month, section)
    cached = get_from_cache(cache_key)
    if cached:
        cached.cache_hit = True
        return cached

    client = Groq(api_key=settings.GROQ_API_KEY)

    # ----------------------------------------------------------
    # Stage 1: Query Rewriting & Metadata Extraction
    # ----------------------------------------------------------
    retrieval_query, query_rewritten = rewrite_query(normalized_prompt, client)

    query_meta = extract_query_metadata(prompt, client)
    if entities:
        if entities.get("states") and not query_meta.get("state"):
            query_meta["state"] = entities["states"][0]
        if entities.get("months") and not query_meta.get("month"):
            query_meta["month"] = entities["months"][0]
        if entities.get("scheme") and not query_meta.get("scheme"):
            query_meta["scheme"] = entities["scheme"]

    effective_state = state or query_meta.get("state")
    effective_month = month or query_meta.get("month")
    effective_scheme = query_meta.get("scheme")

    # ----------------------------------------------------------
    # Stage 2: Hybrid Retrieval
    # ----------------------------------------------------------
    retrieval_start = time.time()

    try:
        vector_chunks = multi_pass_retrieval(
            retrieval_query, effective_state, effective_month, section
        )
    except Exception as e:
        logger.error(
            "Vector retrieval failed",
            **_error_payload(
                "DB_ERROR",
                "Vector retrieval failed. Falling back to BM25.",
                str(e),
                True,
            ),
        )
        vector_chunks = []

    bm25_chunks = bm25_search(retrieval_query, effective_state, effective_month, top_k=10)
    if not bm25_chunks:
        logger.warning("BM25 returned empty results")

    if bm25_chunks:
        raw_chunks = fuse_results(vector_chunks, bm25_chunks)
        retrieval_method = "hybrid"
    else:
        raw_chunks = vector_chunks
        retrieval_method = "vector_only"

    # Scheme-focused metadata filter fallback
    if effective_scheme:
        scheme_filtered = [
            c for c in raw_chunks
            if effective_scheme.lower() in f"{c.get('practice_area', '')} {c.get('chunk_text', '')}".lower()
        ]
        if scheme_filtered:
            raw_chunks = scheme_filtered

    raw_chunks = rank_with_metadata(raw_chunks, effective_state, effective_month, effective_scheme)
    retrieval_latency = round(time.time() - retrieval_start, 4)

    # ----------------------------------------------------------
    # Failure Mode: Case 1 — No Data (strict, no hallucination)
    # ----------------------------------------------------------
    raw_chunk_count = len(raw_chunks)
    logger.info(
        "Chunks retrieved",
        count=raw_chunk_count,
        state=effective_state,
        month=effective_month,
    )
    if not raw_chunks:
        record_query_failure()
        logger.warning(
            "No chunks retrieved — returning no_data (strict mode, no fallback)",
            state=effective_state,
            month=effective_month,
        )
        return _build_no_data_result(
            retrieval_latency=retrieval_latency,
            query_rewritten=query_rewritten,
            retrieval_method=retrieval_method,
            reason="Both vector and BM25 retrieval returned empty for selected filters.",
        )

    # ----------------------------------------------------------
    # Deduplicate & Filter Noise Floor
    # ----------------------------------------------------------
    seen = set()
    unique = []
    for c in raw_chunks:
        key = (c.get("chunk_text", ""))[:100]
        if key not in seen:
            seen.add(key)
            unique.append(c)

    filtered = [c for c in unique if float(c.get("similarity", 0)) >= _NOISE_FLOOR]

    # SAFETY: if filtering removes everything, keep original
    if filtered:
        unique = filtered
    else:
        logger.warning("All chunks below noise floor — retaining original for recall")
        unique = unique

    if not unique:
        logger.warning("All chunks filtered by noise floor", threshold=_NOISE_FLOOR)
        record_query_failure()
        return _build_no_data_result(
            retrieval_latency=retrieval_latency,
            query_rewritten=query_rewritten,
            retrieval_method=retrieval_method,
            reason="All retrieved chunks were below minimum signal threshold.",
        )

    # ----------------------------------------------------------
    # Stage 3: Cross-Encoder Reranking
    # ----------------------------------------------------------
    top_k_cap = min(8, len(unique))
    try:
        reranked, reranker_applied = rerank_with_cross_encoder(
            prompt, unique, top_k=min(8, len(unique))
        )
    except Exception as e:
        logger.error(
            "Reranker failed",
            **_error_payload(
                "LLM_ERROR",
                "Reranker failed. Falling back to diversity ranking.",
                str(e),
                True,
            ),
        )
        reranked = []
        reranker_applied = False

    if not reranker_applied:
        ranked = rerank_diverse(unique)
    else:
        ranked = reranked

    if not ranked:
        logger.warning("Reranker removed all chunks — falling back to pre-ranked")
        ranked = unique[:5]

    # ----------------------------------------------------------
    # Context build
    # ----------------------------------------------------------
    context, context_truncated, sources = build_context(ranked)
    if not context.strip():
        logger.warning("Context empty — rebuilding from raw chunks")
        context = "\n".join([c.get("chunk_text", "") for c in unique[:5]])

    # ----------------------------------------------------------
    # Dual-mode response — select system prompt
    # ----------------------------------------------------------
    avg_similarity = mean([s.similarity for s in sources]) if sources else 0.0
    low_context_mode = avg_similarity < 0.25
    active_system_prompt = (
        LOW_CONTEXT_SYSTEM_PROMPT if low_context_mode else get_system_prompt()
    )
    mode = "relaxed" if low_context_mode else "strict"

    # ----------------------------------------------------------
    # LLM call Output Generation
    # ----------------------------------------------------------
    llm_start = time.time()
    try:
        response = generate_answer(client, active_system_prompt, context, prompt)
    except Exception as e:
        error_info = _error_payload(
            "LLM_ERROR",
            "System temporarily unable to generate response.",
            str(e),
            True,
        )
        logger.error("LLM generation failed", **error_info)
        return _build_rag_error_result(
            answer="System temporarily unable to generate response.",
            retrieval_latency=retrieval_latency,
            query_rewritten=query_rewritten,
            retrieval_method="error",
            details=str(e),
            error_type="LLM_ERROR",
            confidence_reason="No data available",
            justification="LLM generation failed while processing available context.",
        )
    llm_latency = round(time.time() - llm_start, 4)

    answer = response.choices[0].message.content.strip()
    usage = getattr(response, "usage", None)
    tokens_used = usage.prompt_tokens + usage.completion_tokens if usage else 0

    # ----------------------------------------------------------
    # Compute base metrics
    # ----------------------------------------------------------
    similarities = [s.similarity for s in sources]
    retrieval_quality = round(mean(similarities), 4) if similarities else 0.0

    faithfulness = faithfulness_check(answer, context)

    hallucination_risk = round(
        1.0 - (retrieval_quality * (1 if faithfulness else 0.5)), 4
    )

    # ----------------------------------------------------------
    # Evaluation metrics
    # ----------------------------------------------------------
    eval_metrics = evaluate_rag_response(
        similarities=similarities,
        faithfulness_passed=faithfulness,
        retrieval_latency=retrieval_latency,
        llm_latency=llm_latency,
        answer=answer,
    )

    base_confidence = eval_metrics.confidence_score
    status = determine_status(base_confidence)

    # ----------------------------------------------------------
    # Verification layer
    # ----------------------------------------------------------
    verified_answer, verification_passed = verify_response(
        answer=answer,
        sources=sources,
        state=state,
        context_text=context,
    )

    key_points = extract_key_points(verified_answer)

    # ----------------------------------------------------------
    # HYBRID ANALYSIS LAYER
    # ----------------------------------------------------------
    facts = extract_key_facts(ranked)
    analysis = comparative_analysis(ranked)
    enhanced_answer = synthesize_insights(facts, analysis, verified_answer)
    sources_dict = [s.to_dict() for s in sources]
    structured = generate_structured_output(
        client=client,
        prompt=prompt,
        answer=enhanced_answer,
        key_points=key_points,
        sources=sources_dict,
        confidence=base_confidence,
        status=status,
    )

    metadata_match_avg = round(
        mean([float(c.get("_metadata_match_score", 0.0)) for c in ranked]) if ranked else 0.0,
        4,
    )

    final_confidence = calculate_final_confidence(base_confidence, len(sources), retrieval_quality, metadata_match_avg)
    structured["confidence"] = final_confidence

    data_coverage = "limited" if len(sources) <= 2 else ("moderate" if len(sources) <= 6 else "strong")
    structured["data_coverage"] = data_coverage

    # ----------------------------------------------------------
    # Dynamic confidence based on retrieval chunk count
    # ----------------------------------------------------------
    if raw_chunk_count >= 5:
        chunk_confidence_tier = "high"
        confidence_reason = "High confidence due to strong and sufficient supporting evidence."
    elif raw_chunk_count >= 2:
        chunk_confidence_tier = "medium"
        confidence_reason = "Moderate confidence based on partial evidence coverage."
    else:
        chunk_confidence_tier = "low"
        confidence_reason = "Low confidence due to limited retrieved evidence."

    structured["chunk_confidence_tier"] = chunk_confidence_tier
    result = RAGResult(
        answer=enhanced_answer,
        sources=sources,
        chunks_retrieved=raw_chunk_count,
        confidence_score=final_confidence,
        retrieval_quality=retrieval_quality,
        hallucination_risk=hallucination_risk,
        retrieval_latency=retrieval_latency,
        llm_latency=llm_latency,
        tokens_used=tokens_used,
        context_truncated=context_truncated,
        faithfulness_passed=faithfulness,
        cache_hit=False,
        eval_metrics=eval_metrics,
        verification_passed=verification_passed,
        low_context_mode=low_context_mode,
        status=status,
        mode=mode,
        key_points=key_points,
        retrieval_method=retrieval_method,
        reranker_applied=reranker_applied,
        query_rewritten=query_rewritten,
        structured=structured,
        pipeline_latency_ms=round((time.perf_counter() - pipeline_started) * 1000, 2),
        metadata_match_score=metadata_match_avg,
        error=False,
        error_type="",
        message="",
        details="",
        fallback_used=False,
    )
    result.confidence_reason = confidence_reason
    result.data_coverage = data_coverage

    set_in_cache(cache_key, result)

    logger.info("RAG pipeline completed successfully")
    logger.info(
        "Hybrid RAG completed with analysis layer",
        chunks=raw_chunk_count,
        confidence=final_confidence,
        confidence_reason=confidence_reason,
        facts_extracted=len(facts.get("initiatives", [])),
        status=status,
        mode=mode,
        retrieval_method=retrieval_method,
        reranker=reranker_applied,
        query_rewritten=query_rewritten,
        hallucination_risk=hallucination_risk,
        retrieval_latency=retrieval_latency,
        llm_latency=llm_latency,
        tokens=tokens_used,
        low_context_mode=low_context_mode,
        verification_passed=verification_passed,
        key_points_count=len(key_points),
    )

    logger.info("Final pipeline stats",
        raw_chunks=len(raw_chunks),
        unique=len(unique),
        ranked=len(ranked),
        sources=len(sources)
    )

    return result
