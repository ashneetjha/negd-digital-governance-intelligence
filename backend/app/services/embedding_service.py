"""
Embedding Service — generates sentence embeddings using sentence-transformers
and upserts them to Supabase pgvector.
"""

import math
from typing import List
from functools import lru_cache

from app.config import settings
from app.db.database import get_supabase
from app.services.chunking_service import TextChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)


# -----------------------------
# Model Loading
# -----------------------------

@lru_cache(maxsize=1)
def _load_model():
    """Load the embedding model once and cache it."""
    try:
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model", model=settings.EMBEDDING_MODEL)
        return SentenceTransformer(settings.EMBEDDING_MODEL)

    except Exception as exc:
        if settings.STRICT_REAL_AI:
            logger.error(
                "SentenceTransformer unavailable in STRICT_REAL_AI mode",
                error=str(exc),
            )
            raise RuntimeError(
                "Embedding model unavailable while STRICT_REAL_AI=true."
            ) from exc
        logger.warning("SentenceTransformer unavailable, using fallback embeddings", error=str(exc))
        return None


# -----------------------------
# Utilities
# -----------------------------

def _normalize(vector: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


def _fallback_embedding(text: str) -> List[float]:
    """
    Lightweight fallback (non-production): converts text bytes into a bounded
    pseudo-vector with deterministic shape.
    """
    size = settings.EMBEDDING_DIMENSION
    values = [0.0] * size
    data = text.encode("utf-8", errors="ignore")
    for index, b in enumerate(data):
        values[index % size] += ((b / 255.0) * 2.0) - 1.0
    return _normalize(values)


# -----------------------------
# Embedding APIs
# -----------------------------

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = _load_model()

    if model is None:
        if settings.STRICT_REAL_AI:
            raise RuntimeError("Embedding model unavailable while STRICT_REAL_AI=true.")
        return [_fallback_embedding(text) for text in texts]

    embeddings = model.encode(
        texts,
        show_progress_bar=False,
        batch_size=32
    )

    return embeddings.tolist()


def embed_single(text: str) -> List[float]:
    model = _load_model()

    if model is None:
        if settings.STRICT_REAL_AI:
            raise RuntimeError("Embedding model unavailable while STRICT_REAL_AI=true.")
        return _fallback_embedding(text)

    embedding = model.encode([text], show_progress_bar=False)
    return embedding[0].tolist()


# -----------------------------
# Storage Logic
# -----------------------------

def store_chunks(report_id: str, chunks: List[TextChunk]) -> int:
    """
    Embed all chunks and store them in Supabase report_chunks table.
    Returns number of stored chunks.
    """

    if not chunks:
        return 0

    supabase = get_supabase()

    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts)

    records = []

    for chunk, embedding in zip(chunks, embeddings):
        records.append({
            "report_id": report_id,
            "section_type": chunk.section_type,
            "practice_area": chunk.practice_area,
            "chunk_text": chunk.text,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "embedding": embedding,
        })

    # Insert in batches
    batch_size = 50

    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        supabase.table("report_chunks").insert(batch).execute()

    logger.info(
        "Chunks stored",
        report_id=report_id,
        count=len(records)
    )
    return len(records)
