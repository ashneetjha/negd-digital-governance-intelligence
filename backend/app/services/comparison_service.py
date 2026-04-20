"""
Comparison Service — Month-to-Month + Cross-State Governance Comparison
Open-Model | Structured-Extraction Pre-LLM | Citation-Safe | Production Ready

v2.2 Upgrades:
  - Structured data extraction BEFORE LLM call (semi-deterministic comparison)
  - Confidence scoring (numeric 0.0–1.0) for both comparison types
  - Validation ensures both states explicitly referenced
  - Low-confidence fallback for insufficient chunks
"""

import re
from typing import Optional, List, Dict
from statistics import mean
import json
from groq import Groq

from app.config import settings
from app.db.database import get_supabase
from app.services.embedding_service import embed_single
from app.services.retrieval_service import safe_fetch_chunks, normalize_month
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Structured Extraction — Pre-LLM
# ─────────────────────────────────────────────────────────────────────────────
# Extracts structured signals from raw chunks BEFORE they enter the LLM.
# This makes the comparison semi-deterministic by providing pre-computed data.

_KEYWORD_PATTERNS = [
    "DigiLocker", "UMANG", "BharatNet", "Aadhaar", "e-District",
    "DigiYatra", "CERT-In", "MyGov", "STQC", "GIS", "CCTNS",
    "PM Gati Shakti", "Rapid Assessment System", "GIGW", "SeMT",
    "compliance", "audit", "grievance", "blockchain", "AI", "ML",
    "cyber", "cloud", "API", "interoperability",
]

_METRIC_PATTERN = re.compile(
    r"(\d[\d,.]*)\s*(?:%|percent|crore|lakh|million|transactions|users|registrations|services|districts)",
    re.IGNORECASE,
)


def _extract_structured_signals(chunks: List[dict], label: str) -> dict:
    """
    Extract structured governance signals from a list of raw chunks.
    Returns: {initiatives, metrics, keywords, section_types, chunk_count}
    """
    all_text = " ".join(c.get("chunk_text", "") for c in chunks)
    text_lower = all_text.lower()

    # Extract mentioned initiatives
    initiatives = sorted({
        kw for kw in _KEYWORD_PATTERNS if kw.lower() in text_lower
    })

    # Extract quantitative metrics
    metrics = []
    for m in _METRIC_PATTERN.finditer(all_text):
        # Get surrounding context (20 chars before and after)
        start = max(0, m.start() - 30)
        end = min(len(all_text), m.end() + 10)
        context = all_text[start:end].strip()
        metrics.append(context)
    # Deduplicate and limit
    metrics = list(dict.fromkeys(metrics))[:10]

    # Section types present
    section_types = sorted({c.get("section_type", "") for c in chunks if c.get("section_type")})

    # Practice areas
    practice_areas = sorted({c.get("practice_area", "") for c in chunks if c.get("practice_area")})

    return {
        "label": label,
        "chunk_count": len(chunks),
        "initiatives": initiatives,
        "metrics": metrics,
        "keywords": initiatives,  # alias for backward compat
        "section_types": section_types,
        "practice_areas": practice_areas,
    }


def _structured_signals_to_text(signals: dict) -> str:
    """Format structured signals as a concise text block for LLM context."""
    lines = [f"[Structured Data for {signals['label']}]"]
    lines.append(f"  Chunks available: {signals['chunk_count']}")
    if signals["initiatives"]:
        lines.append(f"  Initiatives mentioned: {', '.join(signals['initiatives'])}")
    if signals["metrics"]:
        lines.append(f"  Quantitative data points:")
        for m in signals["metrics"]:
            lines.append(f"    - {m}")
    if signals["section_types"]:
        lines.append(f"  Sections covered: {', '.join(signals['section_types'])}")
    if signals["practice_areas"]:
        lines.append(f"  Practice areas: {', '.join(signals['practice_areas'])}")
    return "\n".join(lines)


def _safe_json_loads(raw_output: str) -> dict:
    """Parse JSON, tolerating markdown code fences from model output."""
    text = (raw_output or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()
    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
# Same-State Comparison
# ─────────────────────────────────────────────────────────────────────────────

_COMPARISON_PROMPT = """
You are a Government Digital Governance Analyst for NeGD / MeitY.

You are comparing TWO monthly reports of the SAME state.

STRICT RULES:
- Use ONLY the provided context.
- Do NOT hallucinate.
- If information is missing, leave arrays empty.
- Output must be valid JSON only.
- No markdown.
- No explanations.
- No extra text outside JSON.

Required JSON format:

{
  "summary": "",
  "new_initiatives": [],
  "removed_mentions": [],
  "quantitative_changes": [
    {"metric": "", "month_a": "", "month_b": ""}
  ],
  "compliance_changes": [
    {"area": "", "status_month_a": "", "status_month_b": ""}
  ],
  "citations": [
    {
      "state": "",
      "reporting_month": "",
      "section_type": "",
      "practice_area": ""
    }
  ]
}
"""


def run_comparison(
    state: str,
    month_a: str,
    month_b: str,
    topic: Optional[str] = None,
    section: Optional[str] = None,
) -> dict:

    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=settings.GROQ_API_KEY)
    supabase = get_supabase()

    query_text = topic or f"initiatives schemes compliance progress changes in {state}"
    query_embedding = embed_single(query_text)

    params = {
        "query_embedding": query_embedding,
        "filter_state": state,
        "filter_month_a": month_a,
        "filter_month_b": month_b,
        "match_count": 14,
    }

    response = supabase.rpc("match_chunks_for_comparison", params).execute()
    chunks: List[dict] = response.data or []

    if not chunks:
        return {
            "summary": f"No report data found for {state} in {month_a} or {month_b}.",
            "new_initiatives": [],
            "removed_mentions": [],
            "quantitative_changes": [],
            "compliance_changes": [],
            "citations": [],
            "confidence": 0.0,
            "status": "no_data",
        }

    # ── Structured extraction pre-LLM ─────────────────────────────────────
    chunks_a = [c for c in chunks if c.get("reporting_month") == month_a]
    chunks_b = [c for c in chunks if c.get("reporting_month") == month_b]
    signals_a = _extract_structured_signals(chunks_a, f"{state} ({month_a})")
    signals_b = _extract_structured_signals(chunks_b, f"{state} ({month_b})")

    # Compute comparison confidence
    sims = [float(c.get("similarity", 0)) for c in chunks]
    avg_sim = mean(sims) if sims else 0.0
    data_score = min(1.0, len(chunks) / 10)
    confidence = round(avg_sim * 0.6 + data_score * 0.4, 4)

    # ── Build context ─────────────────────────────────────────────────────
    context_blocks = []
    # Prepend structured data
    context_blocks.append(_structured_signals_to_text(signals_a))
    context_blocks.append(_structured_signals_to_text(signals_b))
    context_blocks.append("")

    for i, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"[Source {i}]\n"
            f"State: {chunk.get('state')}\n"
            f"Month: {chunk.get('reporting_month')}\n"
            f"Section: {chunk.get('section_type')}\n"
            f"Practice Area: {chunk.get('practice_area')}\n"
            f"Content:\n{chunk.get('chunk_text')}\n"
        )

    context_text = "\n----------------------\n".join(context_blocks)

    full_prompt = (
        f"STATE: {state}\n"
        f"MONTH A: {month_a}\n"
        f"MONTH B: {month_b}\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        "Compare the following structured governance data and raw sources. "
        "Produce the structured JSON comparison."
    )

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _COMPARISON_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.0,
            max_tokens=1500,      # Adjusted for 70b
        )

        raw_output = response.choices[0].message.content.strip()
        parsed = _safe_json_loads(raw_output)
        parsed["confidence"] = confidence
        parsed["status"] = "ok" if confidence >= 0.3 else "low_confidence"

        logger.info(
            "Comparison complete",
            state=state,
            month_a=month_a,
            month_b=month_b,
            chunks=len(chunks),
            confidence=confidence,
        )

        return parsed

    except json.JSONDecodeError:
        logger.error("Groq returned non-JSON output", raw=raw_output[:200])
        return {
            "summary": "Model returned invalid JSON output.",
            "new_initiatives": [],
            "removed_mentions": [],
            "quantitative_changes": [],
            "compliance_changes": [],
            "citations": [],
            "confidence": 0.0,
            "status": "error",
            "error": "Invalid JSON from model",
        }

    except Exception as exc:
        logger.error("Comparison failed", error=str(exc))
        return {
            "summary": "Comparison service temporarily unavailable.",
            "new_initiatives": [],
            "removed_mentions": [],
            "quantitative_changes": [],
            "compliance_changes": [],
            "citations": [],
            "confidence": 0.0,
            "status": "error",
            "error": str(exc),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Cross-State Comparison (v2.2 — structured extraction + hardened)
# ─────────────────────────────────────────────────────────────────────────────

_CROSS_STATE_PROMPT = """
You are a Government Digital Governance Analyst for NeGD / MeitY.

You are comparing governance reports from TWO DIFFERENT STATES.
Structured data has been pre-extracted for each state — use it as primary evidence.

STRICT RULES:
- Use ONLY the provided context and pre-extracted structured data.
- Do NOT hallucinate.
- If information is missing, leave arrays empty.
- You MUST explicitly reference BOTH state names in the summary.
- state_a_summary and state_b_summary MUST each mention their respective state name.
- Do NOT produce vague generic text — be specific with data from context.
- Output must be valid JSON only.
- No markdown.
- No explanations.
- No extra text outside JSON.

Required JSON format:

{
  "summary": "",
  "state_a_summary": "",
  "state_b_summary": "",
  "differences": [],
  "commonalities": [],
  "state_a_strengths": [],
  "state_b_strengths": [],
  "common_initiatives": [],
  "adoption_comparison": [
    {"area": "", "state_a": "", "state_b": ""}
  ],
  "performance_gaps": [
    {"metric": "", "state_a": "", "state_b": "", "leader": ""}
  ],
  "recommendations": [],
  "citations": [
    {
      "state": "",
      "reporting_month": "",
      "section_type": "",
      "practice_area": ""
    }
  ]
}
"""

_MIN_CHUNKS_PER_STATE = 2


def compare_cross_state(
    state_a: str,
    month_a: str,
    state_b: str,
    month_b: str,
    topic: Optional[str] = None,
) -> Dict:
    """
    Compare governance posture of two different states.
    Uses structured extraction pre-LLM for semi-deterministic comparison.
    """
    if not settings.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.")

    client = Groq(api_key=settings.GROQ_API_KEY)
    supabase = get_supabase()

    query_text = topic or "initiatives schemes compliance digital governance progress"
    query_embedding = embed_single(query_text)

    EMPTY_RESULT: Dict = {
        "summary": "Limited comparison due to insufficient data",
        "state_a_summary": "",
        "state_b_summary": "",
        "differences": [],
        "commonalities": [],
        "state_a_strengths": [],
        "state_b_strengths": [],
        "common_initiatives": [],
        "adoption_comparison": [],
        "performance_gaps": [],
        "recommendations": [],
        "confidence": 0.0,
        "citations": [],
        "status": "no_data",
    }

    normalized_state_a = (state_a or "").strip().lower()
    normalized_month_a = normalize_month(month_a)
    normalized_state_b = (state_b or "").strip().lower()
    normalized_month_b = normalize_month(month_b)

    # Retrieve chunks for State A
    params_a = {
        "query_embedding": query_embedding,
        "filter_state": normalized_state_a,
        "filter_month_a": normalized_month_a,
        "filter_month_b": normalized_month_a,
        "match_count": 10,
    }
    resp_a = supabase.rpc("match_chunks_for_comparison", params_a).execute()
    chunks_a: List[dict] = resp_a.data or []
    logger.info("Cross-state retrieval debug", state=normalized_state_a, month=normalized_month_a, results=len(chunks_a))
    if not chunks_a:
        chunks_a = safe_fetch_chunks(state_a, month_a, limit=500)[:10]

    # Retrieve chunks for State B
    params_b = {
        "query_embedding": query_embedding,
        "filter_state": normalized_state_b,
        "filter_month_a": normalized_month_b,
        "filter_month_b": normalized_month_b,
        "match_count": 10,
    }
    resp_b = supabase.rpc("match_chunks_for_comparison", params_b).execute()
    chunks_b: List[dict] = resp_b.data or []
    logger.info("Cross-state retrieval debug", state=normalized_state_b, month=normalized_month_b, results=len(chunks_b))
    if not chunks_b:
        chunks_b = safe_fetch_chunks(state_b, month_b, limit=500)[:10]

    if not chunks_a and not chunks_b:
        return {
            **EMPTY_RESULT,
            "summary": "No data for both states",
            "status": "no_data",
        }

    if not chunks_a or not chunks_b:
        missing_state = state_a if not chunks_a else state_b
        present_state = state_b if not chunks_a else state_a
        return {
            **EMPTY_RESULT,
            "summary": "Limited comparison due to insufficient data",
            "state_a_summary": (
                f"Insufficient data for {state_a}" if not chunks_a else f"Data available for {state_a}"
            ),
            "state_b_summary": (
                f"Insufficient data for {state_b}" if not chunks_b else f"Data available for {state_b}"
            ),
            "status": "low_confidence",
            "confidence": 0.0,
            "recommendations": [
                f"Add or verify report ingestion for {missing_state}",
                f"Re-run comparison after {missing_state} monthly report is available",
                f"Current evidence only supports partial context from {present_state}",
            ],
        }

    # ── Structured extraction pre-LLM ─────────────────────────────────────
    signals_a = _extract_structured_signals(chunks_a, f"{state_a} ({month_a})")
    signals_b = _extract_structured_signals(chunks_b, f"{state_b} ({month_b})")

    # ── Compute confidence (numeric) ──────────────────────────────────────
    sims_a = [float(c.get("similarity", 0)) for c in chunks_a]
    sims_b = [float(c.get("similarity", 0)) for c in chunks_b]
    avg_sim = mean(sims_a + sims_b) if (sims_a or sims_b) else 0.0

    # Data availability score (0–1)
    data_coverage = min(1.0, (len(chunks_a) + len(chunks_b)) / 12)
    # Balance penalty — penalize heavily one-sided comparisons
    balance = min(len(chunks_a), len(chunks_b)) / max(len(chunks_a), len(chunks_b), 1)

    confidence = round(
        avg_sim * 0.40 + data_coverage * 0.35 + balance * 0.25,
        4,
    )

    # Determine confidence tier
    if len(chunks_a) < _MIN_CHUNKS_PER_STATE or len(chunks_b) < _MIN_CHUNKS_PER_STATE:
        confidence_tier = "low"
        confidence = min(confidence, 0.30)
    elif confidence >= 0.6:
        confidence_tier = "high"
    elif confidence >= 0.35:
        confidence_tier = "medium"
    else:
        confidence_tier = "low"

    # ── Build context with structured signals prepended ────────────────────
    context_blocks = []
    context_blocks.append(_structured_signals_to_text(signals_a))
    context_blocks.append(_structured_signals_to_text(signals_b))
    context_blocks.append("")

    for i, chunk in enumerate(chunks_a, start=1):
        context_blocks.append(
            f"[STATE-A Source {i}]\n"
            f"State: {chunk.get('state')}\n"
            f"Month: {chunk.get('reporting_month')}\n"
            f"Section: {chunk.get('section_type')}\n"
            f"Practice Area: {chunk.get('practice_area')}\n"
            f"Content:\n{chunk.get('chunk_text')}\n"
        )

    for i, chunk in enumerate(chunks_b, start=1):
        context_blocks.append(
            f"[STATE-B Source {i}]\n"
            f"State: {chunk.get('state')}\n"
            f"Month: {chunk.get('reporting_month')}\n"
            f"Section: {chunk.get('section_type')}\n"
            f"Practice Area: {chunk.get('practice_area')}\n"
            f"Content:\n{chunk.get('chunk_text')}\n"
        )

    context_text = "\n----------------------\n".join(context_blocks)

    full_prompt = (
        f"STATE A: {state_a} (Month: {month_a})\n"
        f"STATE B: {state_b} (Month: {month_b})\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        "Compare the pre-extracted structured governance data and raw sources. "
        "Produce the structured JSON cross-state comparison."
    )

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _CROSS_STATE_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.0,
            max_tokens=3000,      # Increased for 70b cross-state depth
        )

        raw_output = response.choices[0].message.content.strip()
        parsed = _safe_json_loads(raw_output)

        # Post-validation
        parsed = _validate_cross_state_output(
            parsed, state_a, state_b, confidence, confidence_tier,
            signals_a, signals_b,
        )

        logger.info(
            "Cross-state comparison complete",
            state_a=state_a,
            month_a=month_a,
            state_b=state_b,
            month_b=month_b,
            chunks_a=len(chunks_a),
            chunks_b=len(chunks_b),
            confidence=confidence,
            confidence_tier=confidence_tier,
        )

        return parsed

    except json.JSONDecodeError:
        logger.error("Groq returned non-JSON cross-state output", raw=raw_output[:200])
        return {
            **EMPTY_RESULT,
            "summary": "Model returned invalid JSON output.",
            "status": "error",
            "error": "Invalid JSON from model",
        }

    except Exception as exc:
        logger.error("Cross-state comparison failed", error=str(exc))
        return {
            **EMPTY_RESULT,
            "summary": "Cross-state comparison service temporarily unavailable.",
            "status": "error",
            "error": str(exc),
        }


def _validate_cross_state_output(
    parsed: Dict,
    state_a: str,
    state_b: str,
    confidence: float,
    confidence_tier: str,
    signals_a: dict,
    signals_b: dict,
) -> Dict:
    """
    Post-LLM validation: structural integrity, state references, confidence.
    """
    # Ensure required fields
    required_fields = [
        "summary", "state_a_summary", "state_b_summary",
        "differences", "commonalities", "state_a_strengths", "state_b_strengths",
        "common_initiatives", "adoption_comparison", "performance_gaps",
        "recommendations", "citations",
    ]
    for field in required_fields:
        if field not in parsed:
            parsed[field] = [] if field not in (
                "summary", "state_a_summary", "state_b_summary"
            ) else ""

    # Ensure both states referenced in summary
    summary = parsed.get("summary", "")
    if state_a.lower() not in summary.lower() or state_b.lower() not in summary.lower():
        parsed["summary"] = f"[{state_a} vs {state_b}] {summary}"

    # Ensure state_a_summary references state_a
    sa_summary = parsed.get("state_a_summary", "")
    if sa_summary and state_a.lower() not in sa_summary.lower():
        parsed["state_a_summary"] = f"[{state_a}] {sa_summary}"

    # Ensure state_b_summary references state_b
    sb_summary = parsed.get("state_b_summary", "")
    if sb_summary and state_b.lower() not in sb_summary.lower():
        parsed["state_b_summary"] = f"[{state_b}] {sb_summary}"

    # Inject computed confidence (numeric + tier)
    parsed["confidence"] = confidence
    parsed["confidence_tier"] = confidence_tier

    # If LLM returned commonalities, cross-check with pre-extracted data
    pre_common = sorted(
        set(signals_a.get("initiatives", [])) & set(signals_b.get("initiatives", []))
    )
    if pre_common and not parsed.get("common_initiatives"):
        parsed["common_initiatives"] = pre_common

    # Status
    if confidence_tier == "low":
        parsed["status"] = "low_confidence"
    else:
        parsed["status"] = "ok"

    return parsed