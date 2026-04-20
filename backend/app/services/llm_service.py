import re
import json
import time
from typing import List
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from app.config import settings
from app.utils.logger import get_logger
from app.services.metadata_service import extract_json

logger = get_logger(__name__)

STRUCTURED_TIMEOUT_SECONDS: float = 8.0


def extract_key_points(answer: str) -> List[str]:
    """
    Extract key points from the answer text.
    Looks for bullet points, numbered items, or sentence-level insights.
    """
    points = []

    # Try to find bullet points or numbered items
    lines = answer.split("\n")
    for line in lines:
        stripped = line.strip()
        # Match bullet points: -, *, •, or numbered: 1., 2.
        if re.match(r"^[-*•]\s+.{10,}", stripped):
            points.append(re.sub(r"^[-*•]\s+", "", stripped).strip())
        elif re.match(r"^\d+[.)]\s+.{10,}", stripped):
            points.append(re.sub(r"^\d+[.)]\s+", "", stripped).strip())

    # If no bullet points found, extract first sentence of each paragraph
    if not points:
        paragraphs = [p.strip() for p in answer.split("\n\n") if p.strip()]
        for para in paragraphs[:5]:
            # First sentence
            sentences = re.split(r"[.!?]\s+", para)
            if sentences and len(sentences[0]) > 15:
                points.append(sentences[0].strip().rstrip(".") + ".")

    return points[:7]  # Cap at 7 key points


def faithfulness_check(answer: str, context: str) -> bool:
    if not answer or not context:
        return False

    overlap_count = sum(
        1 for sentence in answer.split(".")
        if len(sentence.strip()) > 20 and sentence.strip()[:40] in context
    )

    return overlap_count >= 1


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
def generate_answer(client: Groq, active_system_prompt: str, context: str, prompt: str):
    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": active_system_prompt},
            {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{prompt}"},
        ],
        temperature=0.0,      # Strict accuracy for governance
        max_tokens=1024,      # Increased for 70b reasoning
        timeout=25.0,         # Increased timeout for larger model
    )

    if not response or not response.choices:
        logger.error("LLM returned empty response")
        raise Exception("Empty LLM response")

    content = response.choices[0].message.content

    if not content or not isinstance(content, str):
        logger.error("Invalid LLM content", content=str(content))
        raise Exception("Invalid LLM output")

    if "<function=" in content or "tool_calls" in content:
        logger.warning("LLM returned tool/function output instead of text")
        raise Exception("Invalid LLM response format")

    return response


def fallback_structured_output(
    answer: str,
    key_points: List[str],
    sources: List[dict],
    confidence: float,
    status: str,
) -> dict:
    change_like = [p for p in key_points if any(w in p.lower() for w in ["increase", "decrease", "change", "improv", "declin"])][:5]
    risk_like = [p for p in key_points if any(w in p.lower() for w in ["risk", "gap", "delay", "issue", "low"])][:5]
    normalized_status = status if status in {"improved", "declined", "stable"} else "stable"
    return {
        "summary": answer[:1200],
        "key_insights": key_points[:7],
        "changes_detected": change_like,
        "risks": risk_like,
        "status": normalized_status,
        "confidence": round(max(0.0, min(confidence, 1.0)), 4),
        "sources": sources,
        "gaps": [],
        "recommendations": [],
        "top_insights": key_points[:3],
    }


def generate_structured_output(
    *,
    client: Groq,
    prompt: str,
    answer: str,
    key_points: List[str],
    sources: List[dict],
    confidence: float,
    status: str,
) -> dict:
    """Force structured governance output schema; fallback parser on malformed output."""
    try:
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            temperature=0.0,
            max_tokens=450,
            timeout=STRUCTURED_TIMEOUT_SECONDS,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Transform governance analysis into strict JSON only with keys: "
                        "summary, key_insights, changes_detected, risks, status, confidence, sources, gaps, recommendations, top_insights. "
                        "status must be one of improved, declined, stable. "
                        "confidence must be a number between 0 and 1."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"User query: {prompt}\n"
                        f"Draft answer: {answer}\n"
                        f"Key points: {json.dumps(key_points)}\n"
                        f"Confidence hint: {confidence}\n"
                        f"Status hint: {status}\n"
                        f"Sources: {json.dumps(sources)}"
                    ),
                },
            ],
        )
        raw_output = response.choices[0].message.content

        logger.debug("Structured raw output", preview=str(raw_output)[:300])

        data = extract_json(raw_output)
        if data and isinstance(data.get("key_insights", []), list):
            parsed_status = str(data.get("status", "stable")).lower()
            if parsed_status not in {"improved", "declined", "stable"}:
                parsed_status = "stable"
            return {
                "summary": data.get("summary", answer),
                "key_insights": data.get("key_insights", key_points[:7]),
                "changes_detected": data.get("changes_detected", []),
                "risks": data.get("risks", []),
                "status": parsed_status,
                "confidence": round(float(data.get("confidence", confidence)), 4),
                "sources": data.get("sources", sources),
                "gaps": data.get("gaps", []),
                "recommendations": data.get("recommendations", []),
                "top_insights": data.get("top_insights", data.get("key_insights", key_points[:3])[:3]),
            }
    except Exception as exc:
        logger.warning(
            "Structured output failed, using fallback",
            error=str(exc),
            answer_preview=answer[:200]
        )

    normalized = "stable"
    if status == "low_confidence":
        normalized = "stable"
    elif any("declin" in kp.lower() or "drop" in kp.lower() for kp in key_points):
        normalized = "declined"
    elif any("improv" in kp.lower() or "increase" in kp.lower() for kp in key_points):
        normalized = "improved"

    return fallback_structured_output(answer, key_points, sources, confidence, normalized)
