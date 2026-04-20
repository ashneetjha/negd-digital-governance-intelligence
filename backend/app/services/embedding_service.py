"""
Embedding service using HuggingFace Inference API only.

This service never generates fake embeddings. On HF failure it returns None so
the rest of the pipeline can fall back to BM25 or store chunks without vectors.
"""

import hashlib
import math
import threading
from typing import Any, Dict, List, Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed

from app.config import settings
from app.db.database import get_supabase
from app.services.chunking_service import TextChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

_HF_MODEL = settings.EMBEDDING_MODEL
_HF_API_URL = f"{settings.HF_API_BASE}/{_HF_MODEL}"
_HF_REQUEST_TIMEOUT = 30.0

_lock = threading.Lock()
_state: Dict[str, Any] = {
    "status": "idle",
    "model": None,
    "error": None,
    "last_attempt": 0.0,
}


def _error_payload(error_type: str, message: str, details: str, fallback_used: bool) -> dict:
    return {
        "error": True,
        "error_type": error_type,
        "message": message,
        "details": details,
        "fallback_used": fallback_used,
    }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def _hf_request(inputs: List[str] | str) -> Any:
    """Call HF Inference API and return parsed JSON or None on failure."""
    try:
        if not settings.HF_API_TOKEN:
            if settings.STRICT_REAL_AI:
                logger.warning("STRICT_REAL_AI: embeddings unavailable, using BM25 only")
            logger.warning("Embedding failed -> using BM25 fallback")
            return None

        headers = {"Authorization": f"Bearer {settings.HF_API_TOKEN}"}
        response = requests.post(
            _HF_API_URL,
            headers=headers,
            json={"inputs": inputs, "options": {"wait_for_model": True}},
            timeout=_HF_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        log_kwargs: dict = {"model": _HF_MODEL, "error": str(exc)}
        if status_code:
            log_kwargs["http_status"] = status_code
        if settings.STRICT_REAL_AI:
            logger.warning("[STRICT_REAL_AI] Embedding API unavailable — falling back to BM25", **log_kwargs)
        else:
            logger.warning("Embedding failed -> using BM25 fallback", **log_kwargs)
        return None


def _mean_pool(vectors: List[List[float]]) -> List[float]:
    if not vectors:
        raise RuntimeError(f"Empty token-vector payload received from {_HF_MODEL}")
    dims = len(vectors[0])
    sums = [0.0] * dims
    for vec in vectors:
        if len(vec) != dims:
            raise RuntimeError(f"Inconsistent token-vector dimensions received from {_HF_MODEL}")
        for i, val in enumerate(vec):
            sums[i] += float(val)
    count = float(len(vectors))
    return [v / count for v in sums]


def _parse_single_embedding(result: Any) -> List[float]:
    if not isinstance(result, list) or not result:
        raise ValueError(f"Unexpected HF API payload: {type(result)}")

    if isinstance(result[0], (int, float)):
        return _finalize_embedding([float(v) for v in result])

    if isinstance(result[0], list):
        inner = result[0]
        if inner and isinstance(inner[0], (int, float)):
            if len(result) != 1:
                raise ValueError(f"Single embedding endpoint returned batch payload: {str(result)[:200]}")
            return _finalize_embedding([float(v) for v in inner])
        if inner and isinstance(inner[0], list):
            if len(result) != 1:
                raise ValueError(f"Single embedding endpoint returned token batch payload: {str(result)[:200]}")
            return _finalize_embedding(_mean_pool([[float(v) for v in tok] for tok in inner]))

    raise ValueError(f"Unable to parse single HF embedding response: {str(result)[:200]}")


def _parse_batch_embeddings(result: Any, expected_batch: int) -> List[List[float]]:
    if not isinstance(result, list) or not result:
        raise ValueError(f"Unexpected HF API batch payload: {type(result)}")

    if isinstance(result[0], (int, float)):
        if expected_batch != 1:
            raise ValueError(f"Batch endpoint returned single vector for {expected_batch} inputs")
        return [_finalize_embedding([float(v) for v in result])]

    if isinstance(result[0], list) and result[0] and isinstance(result[0][0], (int, float)):
        if len(result) != expected_batch:
            raise ValueError(f"HF batch response length {len(result)} does not match input batch {expected_batch}")
        return [_finalize_embedding([float(v) for v in row]) for row in result]

    if isinstance(result[0], list) and result[0] and isinstance(result[0][0], list):
        if len(result) != expected_batch:
            raise ValueError(f"HF token batch response length {len(result)} does not match input batch {expected_batch}")
        return [_finalize_embedding(_mean_pool([[float(v) for v in tok] for tok in item])) for item in result]

    if expected_batch == 1:
        return [_parse_single_embedding(result)]

    raise ValueError(f"Unable to parse batch HF embeddings response: {str(result)[:200]}")


def _normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


def _validate_dimension(vector: List[float]) -> List[float]:
    target = settings.EMBEDDING_DIMENSION
    if len(vector) != target:
        raise RuntimeError(f"Unexpected embedding dimension {len(vector)} from {_HF_MODEL}; expected {target}")
    return vector


def _finalize_embedding(vector: List[float]) -> List[float]:
    return _normalize(_validate_dimension([float(v) for v in vector]))


def _chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def warmup_embedding_model() -> None:
    if settings.HF_API_TOKEN:
        logger.info(
            "HF Inference API configured - embedding mode active",
            model=_HF_MODEL,
            hf_token_prefix=settings.HF_API_TOKEN[:8] + "...",
            strict_mode=settings.STRICT_REAL_AI,
        )
    else:
        logger.error(
            "HF_API_TOKEN is NOT set - embedding service will fall back to BM25 only",
            model=_HF_MODEL,
        )


def get_embedding_status() -> Dict[str, Any]:
    return {
        "status": "hf_api" if settings.HF_API_TOKEN else "unconfigured",
        "loaded": bool(settings.HF_API_TOKEN),
        "error": None if settings.HF_API_TOKEN else "HF_API_TOKEN not set",
        "mode": f"HuggingFace Inference API - {_HF_MODEL}",
        "model": _HF_MODEL,
        "dimension": settings.EMBEDDING_DIMENSION,
        "strict_real_ai": settings.STRICT_REAL_AI,
        "fallback_enabled": False,
    }


def embed_texts(texts: List[str], is_query: bool = False) -> Optional[List[List[float]]]:
    if not texts:
        return []

    try:
        response = _hf_request(texts)
        if response is None:
            return None
        embeddings = _parse_batch_embeddings(response, expected_batch=len(texts))
    except Exception as exc:
        logger.warning(
            "Batch embedding failed - switching to safe fallback",
            **_error_payload(
                "EMBEDDING_FAILURE",
                "Batch embedding failed. Falling back to BM25 retrieval or non-vector storage.",
                str(exc),
                True,
            ),
        )
        return None

    logger.info(
        "Batch embeddings generated",
        model=_HF_MODEL,
        count=len(embeddings),
        mode="query" if is_query else "passage",
    )
    return embeddings


def embed_single(text: str, is_query: bool = True) -> Optional[List[float]]:
    try:
        response = _hf_request(text)
        if response is None:
            return None
        embedding = _parse_single_embedding(response)
    except Exception as exc:
        logger.warning(
            "Single embedding failed - switching to safe fallback",
            **_error_payload(
                "EMBEDDING_FAILURE",
                "Single embedding failed. Falling back to BM25 retrieval.",
                str(exc),
                True,
            ),
        )
        return None

    logger.info(
        "Single embedding generated",
        model=_HF_MODEL,
        text_length=len(text),
        mode="query" if is_query else "passage",
    )
    return embedding


def _get_existing_hashes(report_id: str) -> set:
    try:
        supabase = get_supabase()
        resp = (
            supabase.table("report_chunks")
            .select("chunk_hash")
            .eq("report_id", report_id)
            .execute()
        )
        return {row["chunk_hash"] for row in (resp.data or []) if row.get("chunk_hash")}
    except Exception as exc:
        logger.warning("Could not fetch existing chunk hashes", report_id=report_id, error=str(exc))
        return set()


def _build_chunk_record(
    report_id: str,
    chunk: TextChunk,
    chunk_hash: str,
    state: Optional[str],
    reporting_month: Optional[str],
    scheme: Optional[str],
    embedding: Optional[List[float]],
) -> dict:
    return {
        "report_id": report_id,
        "chunk_text": chunk.text,
        "embedding": embedding,
        "chunk_index": chunk.chunk_index,
        "page_number": chunk.page_number,
        "section_type": chunk.section_type,
        "practice_area": chunk.practice_area,
        "chunk_hash": chunk_hash,
        "state": state,
        "reporting_month": reporting_month,
        "scheme": scheme,
    }


def _insert_chunk_records(supabase, report_id: str, records: List[dict], fallback_used: bool) -> int:
    batch_size = 50
    stored = 0
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table("report_chunks").insert(batch).execute()
            stored += len(batch)
        except Exception as exc:
            logger.error(
                "Insert failed",
                report_id=report_id,
                **_error_payload(
                    "DB_ERROR",
                    "Failed to store chunk records.",
                    str(exc),
                    fallback_used,
                ),
            )
    return stored


def store_chunks(
    report_id: str,
    chunks: List[TextChunk],
    report_metadata: Optional[Dict] = None,
    state: Optional[str] = None,
    reporting_month: Optional[str] = None,
    scheme: Optional[str] = None,
) -> int:
    if not chunks:
        return 0

    supabase = get_supabase()

    if report_metadata:
        state = state or report_metadata.get("state")
        reporting_month = reporting_month or report_metadata.get("reporting_month")
        scheme = scheme or report_metadata.get("scheme")

    if not state or not reporting_month:
        try:
            resp = (
                supabase.table("reports")
                .select("state, reporting_month, scheme")
                .eq("id", report_id)
                .single()
                .execute()
            )
            if resp.data:
                state = state or resp.data.get("state")
                reporting_month = reporting_month or resp.data.get("reporting_month")
                scheme = scheme or resp.data.get("scheme")
        except Exception as exc:
            logger.warning("Metadata fetch failed", error=str(exc))

    existing_hashes = _get_existing_hashes(report_id)
    new_chunks = []
    for chunk in chunks:
        chunk_h = _chunk_hash(chunk.text)
        if chunk_h not in existing_hashes:
            new_chunks.append((chunk, chunk_h))
            existing_hashes.add(chunk_h)

    skipped = len(chunks) - len(new_chunks)
    if not new_chunks:
        logger.info("All chunks duplicate", report_id=report_id)
        return 0

    texts = [chunk.text for chunk, _ in new_chunks]
    embeddings = embed_texts(texts, is_query=False)
    if embeddings is None:
        logger.warning("Embedding unavailable - storing chunks without vectors", report_id=report_id)
        records = [
            _build_chunk_record(report_id, chunk, chunk_h, state, reporting_month, scheme, None)
            for chunk, chunk_h in new_chunks
        ]
        stored = _insert_chunk_records(supabase, report_id, records, fallback_used=True)
        logger.info(
            "Chunks stored",
            report_id=report_id,
            count=stored,
            skipped=skipped,
            state=state,
            vectors_present=False,
        )
        return stored

    records = [
        _build_chunk_record(report_id, chunk, chunk_h, state, reporting_month, scheme, embedding)
        for (chunk, chunk_h), embedding in zip(new_chunks, embeddings)
    ]
    stored = _insert_chunk_records(supabase, report_id, records, fallback_used=False)

    logger.info(
        "Chunks stored",
        report_id=report_id,
        count=stored,
        skipped=skipped,
        state=state,
        vectors_present=True,
    )
    return stored
