"""
Chat service for general governance questions.

Tool calling is disabled for stability.
"""

import time
from typing import List, Optional

from groq import Groq

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_CHATBOT_SYSTEM_PROMPT = """You are a Digital India governance assistant for the NeGD Digital Governance Intelligence Portal, \
built by the National e-Governance Division (NeGD), Ministry of Electronics and Information Technology (MeitY), \
Government of India.

Your expertise:
1. Digital India programme - objectives, pillars, schemes, and current status
2. MeitY / NeGD initiatives - DigiLocker, UMANG, DigiYatra, PM Gati Shakti, DIGIT, etc.
3. State governance digital transformation - SeMT teams, e-Governance, STQC, BharatNet
4. Data governance, cyber security policy, IT Act, Personal Data Protection
5. How to use this portal - uploading reports, running analyses, comparing states, reading citations

Rules:
- Explain policies and systems clearly and accurately.
- Help interpret analytics outputs from this platform.
- Do not fabricate official metrics.
- Never mention knowledge cutoff.
- Never claim lack of real-time data or inability to help.
- If uncertainty exists, provide a general governance policy explanation.
- Keep responses under 400 words unless deeper detail is explicitly required.
- For report-specific data, direct the user to the RAG Analysis feature.
"""


def _error_payload(error_type: str, message: str, details: str, fallback_used: bool) -> dict:
    return {
        "error": True,
        "error_type": error_type,
        "message": message,
        "details": details,
        "fallback_used": fallback_used,
    }


def _fallback_response(details: str, latency_ms: float = 0.0) -> dict:
    error_info = _error_payload(
        "LLM_ERROR",
        "Chat service temporarily unavailable",
        details,
        True,
    )
    logger.error("Chat failed", error=details)
    return {
        "answer": "Chat service temporarily unavailable",
        "sources": [],
        "metadata": {
            "latency_ms": latency_ms,
            "agent": "groq-direct",
            "model": settings.GROQ_MODEL,
            "tool_count": 0,
            "timeout_protected": False,
            "fallback": True,
            "status": "fallback",
        },
        "tokens_used": 0,
        "fallback": True,
        **error_info,
    }


def _build_messages(message: str, history: Optional[List[dict]]) -> list:
    messages = [{"role": "system", "content": _CHATBOT_SYSTEM_PROMPT}]
    for turn in (history or [])[-10:]:
        role = "assistant" if turn.get("role") == "assistant" else "user"
        content = (turn.get("content") or "").strip()
        if content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})
    return messages


def _clean_answer(answer: str) -> str:
    cleaned = (answer or "").replace("**", "").strip()
    cleaned = cleaned.replace("* ", "• ")
    lowered = cleaned.lower()
    if "knowledge cutoff" in lowered or "i don't have" in lowered:
        cleaned = "This answer is based on general governance knowledge."
    paragraphs = [line.strip() for line in cleaned.split("\n") if line.strip()]
    return "\n".join(paragraphs)


def run_chat(
    message: str,
    history: Optional[List[dict]] = None,
) -> dict:
    """
    Run the governance chatbot without tool usage.

    Returns:
        {answer: str, sources: list, metadata: dict, tokens_used: int, ...error fields}
    """
    if not settings.GROQ_API_KEY:
        return _fallback_response("GROQ_API_KEY is not configured.")

    client = Groq(api_key=settings.GROQ_API_KEY)
    messages = _build_messages(message, history)

    start = time.time()
    try:
        completion = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.3,
        )
        latency_ms = round((time.time() - start) * 1000, 1)
        answer = _clean_answer(completion.choices[0].message.content or "")

        result = {
            "answer": answer or "Chat service temporarily unavailable",
            "sources": [],
            "metadata": {
                "latency_ms": latency_ms,
                "agent": "groq-direct",
                "model": settings.GROQ_MODEL,
                "tool_count": 0,
                "timeout_protected": False,
                "fallback": False,
                "status": "ok",
            },
            "tokens_used": 0,
            "error": False,
            "error_type": "",
            "message": "",
            "details": "",
            "fallback_used": False,
        }
        logger.info(
            "Chat response served",
            latency_ms=latency_ms,
            model=settings.GROQ_MODEL,
            fallback=False,
        )
        return result
    except Exception as exc:
        latency_ms = round((time.time() - start) * 1000, 1)
        return _fallback_response(str(exc), latency_ms=latency_ms)
