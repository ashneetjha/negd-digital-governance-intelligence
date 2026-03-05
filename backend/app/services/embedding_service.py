"""
Embedding Service — generates sentence embeddings using sentence-transformers
and upserts them to Supabase pgvector.

Boot-safety design
──────────────────
On Render's free tier the first request may arrive while the CPU is still
loading the SentenceTransformer model (~20-40 s on cold start).  A bare
@lru_cache approach caches a None/exception on the first attempt and never
retries, so the status dashboard permanently shows "Disconnected" even when
the model later becomes available.

Instead we use a thread-safe singleton with explicit state tracking:
  "idle"    – model has never been attempted
  "loading" – a background thread is warming the model right now
  "ready"   – model loaded successfully
  "failed"  – last attempt raised an exception (retried after RETRY_COOLDOWN_S)

The system-status probe calls get_embedding_status() which returns the state
dict without triggering a blocking load, so health checks stay fast.
"""

import math
import threading
import time
from typing import Any, Dict, List

from app.config import settings
from app.db.database import get_supabase
from app.services.chunking_service import TextChunk
from app.utils.logger import get_logger

logger = get_logger(__name__)

# How many seconds to wait before retrying after a failed load
_RETRY_COOLDOWN_S: float = 30.0

# ── Thread-safe singleton state ───────────────────────────────────────────────
_lock = threading.Lock()
_state: Dict[str, Any] = {
    "status": "idle",   # idle | loading | ready | failed
    "model": None,
    "error": None,
    "last_attempt": 0.0,
}


# -----------------------------
# Internal helpers
# -----------------------------

def _do_load() -> None:
    """
    Blocking load executed in a background thread.
    Updates _state in-place; never raises to the caller.
    """
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        logger.info("Loading embedding model", model=settings.EMBEDDING_MODEL)
        model = SentenceTransformer(settings.EMBEDDING_MODEL)

        with _lock:
            _state["model"] = model
            _state["status"] = "ready"
            _state["error"] = None
        logger.info("Embedding model ready", model=settings.EMBEDDING_MODEL)

    except Exception as exc:
        with _lock:
            _state["model"] = None
            _state["status"] = "failed"
            _state["error"] = str(exc)
        logger.error("Embedding model load failed", error=str(exc))


def _ensure_loading() -> None:
    """
    Kick off a background load if one is not already in progress and the
    retry cooldown has elapsed.  Returns immediately (non-blocking).
    """
    with _lock:
        now = time.monotonic()
        if _state["status"] in ("loading", "ready"):
            return
        if _state["status"] == "failed":
            if now - _state["last_attempt"] < _RETRY_COOLDOWN_S:
                return
        _state["status"] = "loading"
        _state["last_attempt"] = now

    t = threading.Thread(target=_do_load, daemon=True, name="embedding-loader")
    t.start()


# -----------------------------
# Public API
# -----------------------------

def warmup_embedding_model() -> None:
    """
    Trigger a non-blocking background warm-up.
    Call this from the FastAPI startup hook so the model is ready
    before the first real request arrives.
    """
    _ensure_loading()


def get_embedding_status() -> Dict[str, Any]:
    """
    Return the current model state dict — safe to call from status probes
    without triggering a blocking load.
    """
    with _lock:
        return {
            "status": _state["status"],
            "loaded": _state["status"] == "ready",
            "error": _state["error"],
        }


def _load_model():
    """
    Return the loaded SentenceTransformer (or None if unavailable).
    Blocks until the model is ready or raises in STRICT_REAL_AI mode.
    Triggers a background load if one hasn't started yet.
    """
    _ensure_loading()

    # Fast-path: already ready
    with _lock:
        if _state["status"] == "ready":
            return _state["model"]

    # Wait up to 90 s for an in-progress load (covers slow CPU cold starts)
    deadline = time.monotonic() + 90.0
    while time.monotonic() < deadline:
        time.sleep(1.0)
        with _lock:
            if _state["status"] == "ready":
                return _state["model"]
            if _state["status"] == "failed":
                break

    # Load failed or timed out
    if settings.STRICT_REAL_AI:
        with _lock:
            err = _state.get("error", "load timed out")
        logger.error(
            "SentenceTransformer unavailable in STRICT_REAL_AI mode",
            error=err,
        )
        raise RuntimeError(
            f"Embedding model unavailable while STRICT_REAL_AI=true: {err}"
        )

    logger.warning(
        "SentenceTransformer unavailable — falling back to pseudo-embeddings",
        error=_state.get("error"),
    )
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
