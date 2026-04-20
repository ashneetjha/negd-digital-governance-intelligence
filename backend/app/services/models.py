from typing import List

class CitationSource:
    def __init__(self, state, month, section, page, similarity):
        self.state = state
        self.month = month
        self.section = section
        self.page = page
        self.similarity = round(float(similarity or 0.0), 4)

    def to_dict(self):
        return {
            "state": self.state,
            "reporting_month": self.month,
            "section_type": self.section,
            "page_number": self.page,
            "similarity_score": self.similarity,
        }

class RAGResult:
    def __init__(
        self,
        answer,
        sources,
        chunks_retrieved,
        confidence_score,
        retrieval_quality,
        hallucination_risk,
        retrieval_latency,
        llm_latency,
        tokens_used,
        context_truncated,
        faithfulness_passed,
        cache_hit,
        eval_metrics=None,
        verification_passed=True,
        low_context_mode=False,
        status="ok",
        mode="strict",
        key_points=None,
        retrieval_method="hybrid",
        reranker_applied=False,
        query_rewritten=False,
        structured=None,
        pipeline_latency_ms=0.0,
        metadata_match_score=0.0,
        error=False,
        error_type="",
        message="",
        details="",
        fallback_used=False,
        data_coverage="limited",
    ):
        self.answer = answer
        self.sources = sources
        self.chunks_retrieved = chunks_retrieved
        self.confidence_score = confidence_score
        self.retrieval_quality = retrieval_quality
        self.hallucination_risk = hallucination_risk
        self.retrieval_latency = retrieval_latency
        self.llm_latency = llm_latency
        self.tokens_used = tokens_used
        self.context_truncated = context_truncated
        self.faithfulness_passed = faithfulness_passed
        self.cache_hit = cache_hit
        self.eval_metrics = eval_metrics
        self.verification_passed = verification_passed
        self.low_context_mode = low_context_mode
        self.status = status
        self.mode = mode
        self.key_points = key_points or []
        self.retrieval_method = retrieval_method
        self.reranker_applied = reranker_applied
        self.query_rewritten = query_rewritten
        self.structured = structured or {}
        self.pipeline_latency_ms = pipeline_latency_ms
        self.metadata_match_score = metadata_match_score
        self.confidence_reason = ""  # populated by run_rag after construction
        self.error = error
        self.error_type = error_type
        self.message = message
        self.details = details
        self.fallback_used = fallback_used
        self.data_coverage = data_coverage

    def to_dict(self, include_eval: bool = False):
        d = {
            "answer": self.answer,
            "key_points": self.key_points,
            "sources": [s.to_dict() for s in self.sources],
            "citations": [s.to_dict() for s in self.sources],
            "chunks_retrieved": self.chunks_retrieved,
            "confidence": self.confidence_score,
            "confidence_score": self.confidence_score,
            "confidence_reason": getattr(self, "confidence_reason", ""),
            "mode": self.mode,
            "status": self.status,
            "retrieval_quality": self.retrieval_quality,
            "hallucination_risk": self.hallucination_risk,
            "retrieval_latency_seconds": self.retrieval_latency,
            "llm_latency_seconds": self.llm_latency,
            "tokens_used": self.tokens_used,
            "context_truncated": self.context_truncated,
            "faithfulness_passed": self.faithfulness_passed,
            "cache_hit": self.cache_hit,
            "verification_passed": self.verification_passed,
            "low_context_mode": self.low_context_mode,
            "retrieval_method": self.retrieval_method,
            "reranker_applied": self.reranker_applied,
            "query_rewritten": self.query_rewritten,
            "structured": self.structured,
            "pipeline_latency_ms": self.pipeline_latency_ms,
            "metadata_match_score": self.metadata_match_score,
            "error": self.error,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "fallback_used": self.fallback_used,
            "data_coverage": getattr(self, "data_coverage", "limited"),
        }
        if include_eval and self.eval_metrics:
            d["eval_metrics"] = self.eval_metrics.to_dict()
        return d
