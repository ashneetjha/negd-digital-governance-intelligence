"""
Verification Service — Post-Response Auditability Layer (v2.1 Hardened)

Checks each RAG response for FOUR integrity conditions:
  1. At least 1 citation source present (no unsupported claims)
  2. Answer text mentions the requested state name (correct scope)
  3. Consistency: "Information not found" only when no sources available
  4. Unsupported claims heuristic: detects specific numeric claims not
     grounded in any source chunk text (simple pattern-based)

If any violation is detected, the answer is replaced with a transparent
safe fallback that lists what was found and acknowledges limited grounding.

NO extra LLM call is used — purely rule-based, <1ms latency impact.
"""

import re
from typing import List, Optional, Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Patterns for unsupported claims detection ─────────────────────────────────
# Matches numeric assertions like "45%", "₹1,200 crore", "3.5 million"
_NUMERIC_CLAIM_PATTERN = re.compile(
    r"\b\d[\d,.]*\s*(?:%|percent|crore|lakh|million|billion|thousand|users|transactions|registrations)\b",
    re.IGNORECASE,
)


# ── Safe fallback templates ───────────────────────────────────────────────────

_SAFE_FALLBACK = (
    "⚠️ Verification Notice: The generated answer did not meet one or more "
    "auditability checks ({violations}). "
    "The following source(s) were retrieved from the document index:\n\n"
    "{source_list}\n\n"
    "Please refine your query or check if the relevant report has been ingested."
)

_NO_SOURCE_FALLBACK = (
    "No relevant document chunks were found in the index for this query. "
    "Please ensure the relevant state report has been ingested, "
    "or broaden your search filters."
)


def verify_response(
    answer: str,
    sources: List,          # List of CitationSource-like objects with .state attribute
    state: Optional[str],
    context_text: str = "",
) -> Tuple[str, bool]:
    """
    Verify a RAG answer against auditability rules.

    Args:
        answer:       The LLM-generated answer string.
        sources:      List of CitationSource objects (must have .state / .month attributes).
        state:        The user-requested state filter (may be None for global queries).
        context_text: The raw context string sent to the LLM (for claim grounding).

    Returns:
        (final_answer, verification_passed)
        - If verification passes: (answer, True)
        - If violation detected:  (safe_fallback, False)
    """
    violations = []

    # ── Rule 1: Citation presence ─────────────────────────────────────────────
    # At least 1 source must be present for a non-"not found" answer
    if not sources and "Information not found" not in answer and "No reports available" not in answer:
        violations.append("no_citation")

    # ── Rule 2: State-scope alignment ─────────────────────────────────────────
    # If state filter was specified, answer should mention the state
    if state and sources:
        state_lower = state.strip().lower()
        answer_lower = answer.lower()
        if state_lower not in answer_lower:
            # Allow if sources have matching state (the answer just didn't spell it out)
            source_states = [getattr(s, "state", "") or "" for s in sources]
            any_matching_source = any(
                state_lower in ss.lower() for ss in source_states if ss
            )
            if not any_matching_source:
                violations.append("state_scope_mismatch")

    # ── Rule 3: Consistency ───────────────────────────────────────────────────
    # Don't say "not found" when sources exist
    if sources and "Information not found" in answer:
        violations.append("consistency_mismatch")

    # ── Rule 4: Unsupported numeric claims ────────────────────────────────────
    # If answer contains specific numbers but context doesn't contain them
    if context_text and sources:
        claims = _NUMERIC_CLAIM_PATTERN.findall(answer)
        if claims:
            ungrounded = []
            for claim in claims:
                # Extract just the numeric part for matching
                num_part = re.search(r"\d[\d,.]*", claim)
                if num_part and num_part.group() not in context_text:
                    ungrounded.append(claim)
            if len(ungrounded) >= 2:
                # Only flag if 2+ ungrounded numeric claims (avoid over-triggering)
                violations.append("unsupported_claims")
                logger.warning(
                    "Unsupported numeric claims detected",
                    claims=ungrounded[:5],
                )

    if not violations:
        return answer, True

    # ── Build fallback ────────────────────────────────────────────────────────
    logger.warning(
        "Verification failed — returning safe fallback",
        violations=violations,
        state=state,
    )

    if not sources:
        return _NO_SOURCE_FALLBACK, False

    source_lines = []
    for i, src in enumerate(sources, 1):
        state_name = getattr(src, "state", "Unknown")
        month = getattr(src, "month", "Unknown")
        section = getattr(src, "section", "—")
        sim = getattr(src, "similarity", None)
        sim_str = f" (similarity: {sim:.3f})" if sim is not None else ""
        source_lines.append(
            f"  {i}. [{state_name} | {month} | {section}]{sim_str}"
        )

    violations_str = ", ".join(violations)
    fallback = _SAFE_FALLBACK.format(
        violations=violations_str,
        source_list="\n".join(source_lines),
    )
    return fallback, False
