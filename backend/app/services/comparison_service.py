"""
Comparison Service — Month-to-Month Governance Comparison
Open-Model | Structured | Citation-Safe | Production Ready
"""

from typing import Optional, List
import json
from groq import Groq

from app.config import settings
from app.db.database import get_supabase
from app.services.embedding_service import embed_single
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------
# Strict Governance Comparison System Prompt
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# Main Comparison Logic
# ---------------------------------------------------------

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

    # -----------------------------------------------------
    # Build semantic search query
    # -----------------------------------------------------

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
        }

    # -----------------------------------------------------
    # Build structured context
    # -----------------------------------------------------

    context_blocks = []

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
        "Produce the structured JSON comparison."
    )

    # -----------------------------------------------------
    # Call Groq LLaMA (Deterministic)
    # -----------------------------------------------------

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _COMPARISON_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.0,
            max_tokens=2000,
        )

        raw_output = response.choices[0].message.content.strip()

        parsed = json.loads(raw_output)

        logger.info(
            "Comparison complete",
            state=state,
            month_a=month_a,
            month_b=month_b,
            chunks=len(chunks),
        )

        return parsed

    except json.JSONDecodeError:
        logger.error("Groq returned non-JSON output", raw=raw_output)

        return {
            "summary": "Model returned invalid JSON output.",
            "new_initiatives": [],
            "removed_mentions": [],
            "quantitative_changes": [],
            "compliance_changes": [],
            "citations": [],
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
            "error": str(exc),
        }