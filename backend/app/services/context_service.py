from pathlib import Path
from typing import List, Tuple
from app.services.models import CitationSource

SIMILARITY_THRESHOLD: float = 0.25
MAX_CONTEXT_CHARS: int = 8000
MAX_CHUNKS = 8

_SYSTEM_PROMPT_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "ml"
    / "prompts"
    / "system_prompt.txt"
)

_SYSTEM_PROMPT = ""

def get_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if not _SYSTEM_PROMPT:
        try:
            _SYSTEM_PROMPT = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        except Exception:
            _SYSTEM_PROMPT = (
                "You are a Government Digital Governance Analyst.\n"
                "Use ONLY the provided context.\n"
                "Do NOT hallucinate.\n"
                "If information is missing respond exactly:\n"
                "'Information not found in selected reports.'\n"
                "Cite State and Reporting Month clearly.\n"
            )
    return _SYSTEM_PROMPT

LOW_CONTEXT_SYSTEM_PROMPT = (
    "You are a Digital Governance Intelligence Assistant for NeGD / MeitY.\n\n"
    "IMPORTANT: The retrieved context for this query has LIMITED or LOW-CONFIDENCE evidence.\n"
    "Respond using whatever partial information is available. Be transparent about limitations.\n\n"
    "RULES:\n"
    "- Use ONLY the provided context chunks (partial as they may be).\n"
    "- Begin your answer with: \"Based on limited available evidence:\"\n"
    "- State clearly what was and was NOT found.\n"
    "- Do NOT hallucinate or invent missing data.\n"
    "- Include a Sources section citing the chunks that were used.\n"
    "- Do NOT refuse to answer — provide best-effort partial analysis.\n"
)

def build_context(ranked_chunks: List[dict]) -> Tuple[str, bool, List[CitationSource]]:
    """Builds the string context and captures citations."""
    total = 0
    context_truncated = False
    context_blocks = []
    sources = []

    for i, chunk in enumerate(ranked_chunks[:MAX_CHUNKS], start=1):
        text = chunk.get("chunk_text", "").strip()
        if not text:
            continue

        state_val = chunk.get('state') or 'Unknown'
        month_val = chunk.get('reporting_month') or 'Unknown'
        section_val = chunk.get('section_type') or 'Unknown'
        page_val = chunk.get('page_number')
        page_str = f" | Page: {page_val}" if page_val else ""

        block = (
            f"[State: {state_val} | Month: {month_val} | Section: {section_val}{page_str}]\n"
            f"{text}\n"
        )
        if total + len(block) > MAX_CONTEXT_CHARS:
            context_truncated = True
            break

        total += len(block)
        context_blocks.append(block)
        sources.append(
            CitationSource(
                chunk.get("state") or "Unknown",
                chunk.get("reporting_month") or "Unknown",
                chunk.get("section_type") or "Unknown",
                chunk.get("page_number"),
                float(chunk.get("similarity", 0.0)),
            )
        )

    if not context_blocks:
        return "", False, []

    context = "\n-----------------\n".join(context_blocks)
    return context, context_truncated, sources
