import re
import time
from typing import Dict, List, Optional

from app.config import settings
from app.db.database import get_supabase
from app.services.embedding_service import embed_single
from app.services.query_service import expand_query
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Lazy BM25 index cache: {state_key: {"bm25": BM25Okapi, "chunks": [...], "ts": float}}
_BM25_CACHE: Dict[str, dict] = {}
_BM25_CACHE_TTL = 600  # 10 minutes

_bm25_available = True
try:
    from rank_bm25 import BM25Okapi
except ImportError:
    _bm25_available = False
    logger.error("BM25 not installed")
    raise ImportError("BM25 not installed. Run: pip install rank_bm25")


def _error_payload(error_type: str, message: str, details: str, fallback_used: bool) -> dict:
    return {
        "error": True,
        "error_type": error_type,
        "message": message,
        "details": details,
        "fallback_used": fallback_used,
    }


def tokenize(text: str) -> List[str]:
    text = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = text.split()
    return [t for t in tokens if len(t) > 2]


def normalize_month(month: Optional[str]) -> Optional[str]:
    """Normalize supported month inputs to YYYY-MM."""
    if not month:
        return None

    raw = month.strip()
    if not raw:
        return None

    match = re.match(r"^(20\d{2})-(\d{1,2})$", raw)
    if match:
        year = int(match.group(1))
        month_num = int(match.group(2))
        if 1 <= month_num <= 12:
            return f"{year:04d}-{month_num:02d}"

    for fmt in ("%B %Y", "%b %Y"):
        try:
            parsed = time.strptime(raw, fmt)
            return f"{parsed.tm_year:04d}-{parsed.tm_mon:02d}"
        except ValueError:
            continue

    return raw


def safe_fetch_chunks(state: Optional[str], month: Optional[str], limit: int = 500) -> List[dict]:
    """
    Strict filter retrieval — NEVER falls back to full corpus when filters are set.
    Returns empty list if no matching data exists for the given state/month.
    """
    try:
        supabase = get_supabase()
        normalized_state = state.strip().lower() if state else None
        normalized_month = normalize_month(month)

        logger.info(
            "Retrieval attempt",
            state=normalized_state,
            month=normalized_month,
        )

        # Step 1: state + month (strict — both must match)
        query = supabase.table("report_chunks").select(
            "id, chunk_text, state, reporting_month, section_type, practice_area, page_number"
        )
        if normalized_state:
            query = query.ilike("state", normalized_state)
        if normalized_month:
            query = query.eq("reporting_month", normalized_month)

        raw_rows = query.limit(limit).execute().data or []
        rows = []
        for row in raw_rows:
            if not row.get("chunk_text"):
                continue
            row_state = str(row.get("state") or "").strip().lower()
            row_month = normalize_month(str(row.get("reporting_month") or ""))
            if normalized_state and row_state != normalized_state:
                continue
            if normalized_month and row_month != normalized_month:
                continue
            rows.append(row)

        logger.info(
            "Chunks found",
            count=len(rows),
            state=normalized_state,
            month=normalized_month,
        )
        if rows:
            return rows

        # Step 2: state-only fallback
        if normalized_state:
            logger.info("Retrieval attempt", state=normalized_state, month=None)
            step2 = (
                supabase.table("report_chunks")
                .select("id, chunk_text, state, reporting_month, section_type, practice_area, page_number")
                .ilike("state", normalized_state)
                .limit(limit)
                .execute()
            )
            raw_rows_state_only = step2.data or []
            rows_state_only = []
            for row in raw_rows_state_only:
                if not row.get("chunk_text"):
                    continue
                row_state = str(row.get("state") or "").strip().lower()
                if row_state == normalized_state:
                    rows_state_only.append(row)

            logger.info(
                "Chunks found",
                count=len(rows_state_only),
                state=normalized_state,
                month=None,
            )
            if rows_state_only:
                return rows_state_only

        # Step 3: no fallback to full corpus — keep precision
        return []
    except Exception as exc:
        logger.error("Retrieval failed", error=str(exc))
        return []


def _fetch_bm25_chunks(state: Optional[str], month: Optional[str]) -> List[dict]:
    """Fetch retrieval chunks with safe state/month fallback only."""
    return safe_fetch_chunks(state, month, limit=500)


def build_bm25_index(state: Optional[str], month: Optional[str]) -> Optional[dict]:
    """
    Build an in-memory BM25 index from DB chunks for the given state/month.
    Cached with TTL. Returns None if BM25 is unavailable or no documents found.
    """
    if not _bm25_available:
        return None

    normalized_state = state.strip().lower() if state else None
    normalized_month = normalize_month(month)
    cache_key = f"{normalized_state or 'all'}|{normalized_month or 'all'}"
    cached = _BM25_CACHE.get(cache_key)
    if cached and (time.time() - cached["ts"]) < _BM25_CACHE_TTL:
        return cached

    try:
        chunks = _fetch_bm25_chunks(state, month)
        if not chunks:
            # DO NOT initialize BM25 with empty corpus — log and return None
            logger.warning(
                "BM25 index skipped — no documents found for filters",
                state=state,
                month=month,
            )
            return None

        corpus = [tokenize(c.get("chunk_text", "")) for c in chunks]
        # Safety: skip index if all tokens are empty
        if not any(corpus):
            logger.warning("BM25 index skipped — all chunks produce empty token lists", state=state, month=month)
            return None

        bm25 = BM25Okapi(corpus)

        result = {"bm25": bm25, "chunks": chunks, "ts": time.time()}
        _BM25_CACHE[cache_key] = result

        logger.info("BM25 index built", state=state, month=month, chunks=len(chunks))
        return result
    except Exception as exc:
        logger.warning(
            "BM25 index build failed",
            **_error_payload(
                "DB_ERROR",
                "Failed to build BM25 index.",
                str(exc),
                True,
            ),
        )
        return None


def bm25_search(
    query: str, state: Optional[str], month: Optional[str], top_k: int = 10
) -> List[dict]:
    """
    Run BM25 keyword search. Returns chunks with normalized bm25_score.
    Returns empty list on any failure.
    """
    index = build_bm25_index(state, month)
    if not index:
        return []

    try:
        tokens = tokenize(query)
        scores = index["bm25"].get_scores(tokens)
        chunks = index["chunks"]

        scored = [(chunks[i], float(scores[i])) for i in range(len(chunks))]
        scored.sort(key=lambda x: x[1], reverse=True)

        max_score = scored[0][1] if scored else 1.0
        if max_score == 0:
            max_score = 1.0

        result = []
        for chunk, score in scored[:top_k]:
            chunk_copy = dict(chunk)
            chunk_copy["bm25_score"] = round(score / max_score, 4)
            result.append(chunk_copy)

        return result
    except Exception as exc:
        logger.warning(
            "BM25 search failed",
            **_error_payload(
                "DB_ERROR",
                "BM25 search failed.",
                str(exc),
                True,
            ),
        )
        return []


def retrieve_once(query_embedding, state, month, section, top_k, query_text: Optional[str] = None):
    safe_top_k = min(top_k, 8)
    if query_embedding is None:
        logger.warning("Embedding unavailable - using BM25-only retrieval", state=state, month=month)
        try:
            return bm25_search(query_text or "", state, month, top_k=safe_top_k)
        except Exception as exc:
            error_info = _error_payload(
                "EMBEDDING_FAILURE",
                "Embedding unavailable and BM25 fallback failed.",
                str(exc),
                True,
            )
            logger.error("BM25 fallback failed", **error_info)
            return []

    supabase = get_supabase()
    params = {
        "query_embedding": query_embedding,
        "match_count": safe_top_k,
        "filter_state": state,
        "filter_month": month,
        "filter_section": section,
    }

    try:
        response = supabase.rpc("match_chunks", params).execute()
        return response.data or []
    except Exception as exc:
        error_info = _error_payload(
            "DB_ERROR",
            "Vector retrieval failed. Attempting BM25 fallback.",
            str(exc),
            True,
        )
        logger.error("DB Error executing match_chunks", **error_info)
        try:
            return bm25_search(query_text or "", state, month, top_k=safe_top_k)
        except Exception as fallback_exc:
            fallback_error = _error_payload(
                "DB_ERROR",
                "BM25 fallback failed after vector retrieval error.",
                str(fallback_exc),
                True,
            )
            logger.error("BM25 fallback failed", **fallback_error)
            return []


def multi_pass_retrieval(prompt: str, state: Optional[str], month: Optional[str], section: Optional[str]):
    expanded = expand_query(prompt)
    results = []
    embedding_failures = 0

    for q in expanded:
        try:
            emb = embed_single(q, is_query=True)
            if emb is None:
                embedding_failures += 1
                logger.warning(
                    "Embedding unavailable for query. System will fallback to BM25",
                    query=q,
                    failure_count=embedding_failures,
                )
                results.extend(
                    retrieve_once(None, state, month, section, settings.RAG_TOP_K, query_text=q)
                )
                continue

            chunks = retrieve_once(
                emb, state, month, section, settings.RAG_TOP_K, query_text=q
            )
            results.extend(chunks)
        except Exception as exc:
            embedding_failures += 1
            error_info = _error_payload(
                "EMBEDDING_FAILURE",
                "Vector embedding failed for query. Attempting BM25 fallback.",
                str(exc),
                True,
            )
            logger.error(
                "Vector embedding failed for query. System will fallback to BM25 or skip query expansion pass",
                query=q,
                failure_count=embedding_failures,
                **error_info,
            )
            try:
                results.extend(bm25_search(q, state, month, top_k=settings.RAG_TOP_K))
            except Exception as fallback_exc:
                fallback_error = _error_payload(
                    "EMBEDDING_FAILURE",
                    "BM25 fallback failed after embedding error.",
                    str(fallback_exc),
                    True,
                )
                logger.error("BM25 fallback failed", query=q, **fallback_error)

    if embedding_failures > 0:
        logger.warning(
            f"Total {embedding_failures} embedding failures encountered during vector retrieval."
        )

    if not results:
        logger.warning("Vector retrieval returned no results - fallback to BM25")
        bm25_results = bm25_search(prompt, state, month, top_k=settings.RAG_TOP_K)
        return bm25_results

    return results


def fuse_results(
    vector_chunks: List[dict],
    bm25_chunks: List[dict],
    vector_weight: float = 0.5,
    bm25_weight: float = 0.5,
) -> List[dict]:
    """
    Fuse vector and BM25 results using weighted score combination.
    Deduplicates by chunk text prefix (first 100 chars).
    """
    if not vector_chunks:
        vector_weight = 0.0
        bm25_weight = 1.0
    elif not bm25_chunks:
        vector_weight = 1.0
        bm25_weight = 0.0

    scores: Dict[str, dict] = {}

    for c in vector_chunks:
        key = (c.get("chunk_text", ""))[:100]
        if key not in scores:
            scores[key] = {
                "chunk": c,
                "vector_score": float(c.get("similarity", 0)),
                "bm25_score": 0.0,
            }
        else:
            scores[key]["vector_score"] = max(
                scores[key]["vector_score"], float(c.get("similarity", 0))
            )

    for c in bm25_chunks:
        key = (c.get("chunk_text", ""))[:100]
        if key not in scores:
            scores[key] = {
                "chunk": c,
                "vector_score": 0.0,
                "bm25_score": float(c.get("bm25_score", 0)),
            }
        else:
            scores[key]["bm25_score"] = max(
                scores[key]["bm25_score"], float(c.get("bm25_score", 0))
            )

    fused = []
    for entry in scores.values():
        final = (
            entry["vector_score"] * vector_weight
            + entry["bm25_score"] * bm25_weight
        )
        chunk = dict(entry["chunk"])
        chunk["similarity"] = round(final, 4)
        chunk["_vector_score"] = entry["vector_score"]
        chunk["_bm25_score"] = entry["bm25_score"]
        fused.append(chunk)

    fused.sort(key=lambda x: float(x.get("similarity", 0)), reverse=True)
    return fused


def recency_score(reporting_month: Optional[str]) -> float:
    if not reporting_month or not re.match(r"^20\d{2}-(0[1-9]|1[0-2])$", reporting_month):
        return 0.0
    year, month = reporting_month.split("-")
    y = int(year)
    m = int(month)
    now = time.gmtime()
    months_diff = max(0, (now.tm_year - y) * 12 + (now.tm_mon - m))
    return round(max(0.0, 1.0 - min(months_diff, 48) / 48), 4)


def metadata_match_score(chunk: dict, state: Optional[str], month: Optional[str], scheme: Optional[str]) -> float:
    score = 0.0
    if state and chunk.get("state") and str(chunk.get("state")).lower() == state.lower():
        score += 0.4
    if month and chunk.get("reporting_month") and str(chunk.get("reporting_month")) == month:
        score += 0.3
    if scheme:
        hay = f"{chunk.get('practice_area', '')} {chunk.get('chunk_text', '')}".lower()
        if scheme.lower() in hay:
            score += 0.3
    return round(min(1.0, score), 4)


def rank_with_metadata(chunks: List[dict], state: Optional[str], month: Optional[str], scheme: Optional[str]) -> List[dict]:
    """Re-rank chunks by relevance + recency + metadata match."""
    ranked = []
    for c in chunks:
        relevance = float(c.get("similarity", 0.0))
        recency = recency_score(c.get("reporting_month"))
        metadata_score_val = metadata_match_score(c, state, month, scheme)
        final = round(relevance * 0.7 + recency * 0.15 + metadata_score_val * 0.15, 4)
        c2 = dict(c)
        c2["_metadata_match_score"] = metadata_score_val
        c2["_recency_score"] = recency
        c2["similarity"] = final
        ranked.append(c2)
    ranked.sort(key=lambda x: float(x.get("similarity", 0.0)), reverse=True)
    return ranked
