import re
import time
from typing import List, Tuple
from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

def normalize_query(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().lower())

def expand_query(prompt: str) -> List[str]:
    return [
        prompt,
        f"Governance progress regarding {prompt}",
        f"Compliance and implementation details about {prompt}",
    ]

def rewrite_query(prompt: str, client: Groq) -> Tuple[str, bool]:
    """
    Use LLM to rewrite query for better retrieval.
    Returns (rewritten_query, was_rewritten).
    Falls back to original prompt on any failure.
    """
    try:
        start = time.time()
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a query rewriter for a government digital governance report database. "
                        "Rewrite the user's query to improve document retrieval. "
                        "Keep the core intent but add relevant governance terminology. "
                        "Output ONLY the rewritten query — no explanations, no quotes."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=150,
            timeout=5.0,  # Strict 5s timeout for rewriting
        )
        elapsed = time.time() - start
        rewritten = response.choices[0].message.content.strip()

        # Safety: reject if rewrite is empty or too long or too different
        if not rewritten or len(rewritten) > 500:
            return prompt, False

        logger.info(
            "Query rewritten",
            original=prompt[:50],
            rewritten=rewritten[:50],
            latency_ms=round(elapsed * 1000),
        )
        return rewritten, True

    except Exception as exc:
        logger.warning("Query rewriting failed — using original", error=str(exc))
        return prompt, False
