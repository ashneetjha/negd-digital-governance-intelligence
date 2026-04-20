from typing import List, Tuple
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

HF_RERANKER_URL = (
    "https://api-inference.huggingface.co/models/"
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)
HF_RERANKER_TIMEOUT = 8.0  # seconds

def rerank_diverse(chunks: List[dict]) -> List[dict]:
    """Fallback diversity reranking logic if HP API fails."""
    sorted_chunks = sorted(
        chunks,
        key=lambda x: float(x.get("similarity", 0)),
        reverse=True,
    )

    seen_sections = set()
    diverse = []

    for c in sorted_chunks:
        section = c.get("section_type")
        if section not in seen_sections:
            diverse.append(c)
            seen_sections.add(section)

    return diverse if diverse else sorted_chunks[:5]

def rerank_with_cross_encoder(
    query: str, chunks: List[dict], top_k: int = 5
) -> Tuple[List[dict], bool]:
    """
    Rerank chunks using cross-encoder via HF Inference API.
    Returns (reranked_chunks, was_reranked).
    Falls back to input order on any failure.
    """
    if not settings.HF_API_TOKEN or not chunks:
        return chunks[:top_k], False

    try:
        import requests as req

        # Prepare pairs for cross-encoder
        inputs = [
            {"text": query, "text_pair": c.get("chunk_text", "")[:512]}
            for c in chunks[:10]  # Limit to top 10 for reranking
        ]

        response = req.post(
            HF_RERANKER_URL,
            headers={"Authorization": f"Bearer {settings.HF_API_TOKEN}"},
            json={"inputs": inputs, "options": {"wait_for_model": True}},
            timeout=HF_RERANKER_TIMEOUT,
        )
        response.raise_for_status()
        scores = response.json()

        # HF cross-encoder returns list of [{"label": ..., "score": float}]
        # or list of floats depending on model
        rerank_scores = []
        for s in scores:
            if isinstance(s, (int, float)):
                rerank_scores.append(float(s))
            elif isinstance(s, list) and s:
                # Classification output: pick highest score
                if isinstance(s[0], dict):
                    rerank_scores.append(float(s[0].get("score", 0)))
                else:
                    rerank_scores.append(float(s[0]))
            elif isinstance(s, dict):
                rerank_scores.append(float(s.get("score", 0)))
            else:
                rerank_scores.append(0.0)

        # Pair with chunks and sort
        paired = list(zip(chunks[:10], rerank_scores))
        paired.sort(key=lambda x: x[1], reverse=True)

        reranked = []
        for chunk, score in paired[:top_k]:
            c = dict(chunk)
            c["rerank_score"] = round(score, 4)
            reranked.append(c)

        logger.info(
            "Cross-encoder reranking applied",
            input_chunks=len(chunks[:10]),
            output_chunks=len(reranked),
            top_score=round(paired[0][1], 4) if paired else 0,
        )
        return reranked, True

    except Exception as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        log_kwargs: dict = {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2", "error": str(exc)}
        if status_code:
            log_kwargs["http_status"] = status_code
        logger.warning("Cross-encoder reranking failed — using original ranking (safe fallback)", **log_kwargs)
        return chunks[:top_k], False
